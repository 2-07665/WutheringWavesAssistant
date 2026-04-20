import logging
import multiprocessing
import queue
import sys
import threading
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Callable, Dict, Optional, Any, List

from src.config.gui_config import ParamConfig
from src.core.geometry import Scaler
from src.core.interface import WindowService, ImgService, OCRService, ControlService, ODService, BossInfoService, \
    PageService, EchoMergeService, GlobalPageService, CombatService
from src.core.pages import I18nTr

logger = logging.getLogger(__name__)


@dataclass
class RuntimeContext:
    current_node: Optional[str] = None
    start_time: float = field(default_factory=time.time)
    stop_event: threading.Event = field(default_factory=threading.Event)


@dataclass
class StatsContext:
    node_runs: Dict[str, int] = field(default_factory=dict)
    node_time: Dict[str, float] = field(default_factory=dict)
    retries: Dict[str, int] = field(default_factory=dict)


@dataclass
class SharedContext:
    fight_count: int = 0
    boss_name: Optional[str] = None
    last_result: Optional[Any] = None

    # 登录时是否移动窗口
    login_mv_window: bool = field(default=False)


# @dataclass(frozen=True)
@dataclass
class TaskSpec:
    # 节点唯一id
    run_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    task_name: Optional[str] = None
    # 主进程id
    leader_pid: Optional[int] = None
    # gui窗口id
    gui_win_id: Optional[int] = None
    # 启动参数
    cli_args: Optional[List[Any]] = None
    # 系统
    platform: str = sys.platform
    device: Optional[str] = None
    # 游戏路径，用于重启游戏
    game_path: Optional[str] = None
    # 配置文件
    param_config_path: Optional[str] = None
    param_config: Optional[str] = None
    # 是否开启自动跳过
    skip_is_open: Optional[bool] = None
    # ocr是否使用gpu
    ocr_use_gpu: Optional[bool] = None


@dataclass
class IPCManager:
    log_queue: Optional[multiprocessing.Queue] = None
    event_queue: Optional[multiprocessing.Queue] | Optional[queue.Queue] = None
    # progress_queue: Optional[multiprocessing.Queue] = None


@dataclass
class NodeContext:
    runtime: RuntimeContext = field(default_factory=RuntimeContext)
    stats: StatsContext = field(default_factory=StatsContext)
    shared: SharedContext = field(default_factory=SharedContext)

    spec: TaskSpec = field(default_factory=TaskSpec)
    ipc: Optional[IPCManager] = field(default=None)

    extra: dict = field(default_factory=dict)

    _container: Optional[Any] = field(default=None, repr=False)
    _param_config: ParamConfig = field(default_factory=ParamConfig.build)

    @property
    def window_service(self) -> WindowService:
        return self._container.window_service()

    @property
    def img_service(self) -> ImgService:
        return self._container.img_service()

    @property
    def ocr_service(self) -> OCRService:
        return self._container.ocr_service()

    @property
    def control_service(self) -> ControlService:
        return self._container.control_service()

    @property
    def od_service(self) -> ODService:
        return self._container.od_service()

    @property
    def page_event_service(self) -> PageService:
        return self._container.page_event_service()

    @property
    def boss_info_service(self) -> BossInfoService:
        return self._container.boss_info_service()

    @property
    def page_service(self) -> GlobalPageService:
        return self._container.page_service()

    @property
    def echo_merge_service(self) -> EchoMergeService:
        return self._container.echo_merge_service()

    @property
    def combat_service(self) -> CombatService:
        return self._container.combat_service()

    # --------------- runtime ------------------

    @property
    def param_config(self) -> ParamConfig:
        # 优先使用快照参数
        if self.spec.param_config:
            self._param_config = ParamConfig.build(content=self.spec.param_config)
        return self._param_config

    # --------------- Shortcut ------------------

    @property
    def scaler(self) -> Scaler:
        return self.window_service.scaler

    @property
    def tr(self) -> I18nTr:
        return self.window_service.tr


@dataclass
class Transition:
    condition: Callable[[NodeContext], bool]
    dst: Optional[str]
    name: str = ""


# Node 注册器
NODE_REGISTRY: Dict[str, "Node"] = {}


class Node:

    def __init__(
            self,
            func: Callable,
            name: str,
            retry: int = 0,
            timeout: Optional[int] = None,
    ):
        self.func = func
        self.name = name
        self.retry = retry
        self.timeout = timeout

    def run(self, ctx: NodeContext):
        attempts = 0
        while True:
            attempts += 1
            start = time.monotonic()
            try:
                if self.timeout and self.timeout > 0:
                    result = self._wait_until(ctx, lambda: self.func(ctx), timeout=self.timeout)
                else:
                    result = self.func(ctx)
                duration = time.monotonic() - start
                ctx.stats.node_time[self.name] = ctx.stats.node_time.get(self.name, 0) + duration
                return result
            except Exception as e:
                ctx.stats.retries[self.name] = ctx.stats.retries.get(self.name, 0) + 1
                if attempts > self.retry:
                    raise e
                logger.info(f"[NODE] retry {self.name} ({attempts}/{self.retry})")

    def _wait_until(
            self,
            ctx: NodeContext,
            condition: Callable,
            timeout: float,
            interval: float = 0.1,
    ) -> bool:
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            if ctx.runtime.stop_event.is_set():
                return False
            if condition(ctx):
                return True
            time.sleep(interval)
        return False


def node(name: str = None, retry: int = 0, timeout: int = None):
    """
    Node 装饰器
    :param name:
    :param retry:
    :param timeout:
    :return:
    """

    def decorator(func):
        node_name = name or func.__name__
        NODE_REGISTRY[node_name] = Node(
            func,
            node_name,
            retry=retry,
            timeout=timeout,
        )
        logger.debug(f"register node: {node_name}")
        return func

    return decorator


class WorkflowEngine:
    """
    Workflow Engine
    """

    def __init__(self):
        self.transitions = {}

    def source(self, src: str):
        return TransitionBuilder(self, src)

    def add_transition(self, src, condition, dst, name=""):
        self.transitions.setdefault(src, []).append(
            Transition(condition, dst, name)
        )

    def run(self, ctx: NodeContext, start_node: str):
        current = start_node
        while current:
            if not ctx.runtime.stop_event.is_set():
                logger.debug("[ENGINE] stopped")
                break
            node = NODE_REGISTRY[current]
            ctx.runtime.current_node = current
            ctx.stats.node_runs[current] = ctx.stats.node_runs.get(current, 0) + 1
            logger.debug(f"[ENGINE] run: {current}")
            result = node.run(ctx)
            ctx.shared.last_result = result
            logger.debug(f"[ENGINE] result: {result}")
            next_node = None
            for trans in self.transitions.get(current, []):
                if trans.condition(ctx):
                    logger.debug(f"[ENGINE] hit: {trans.name}")
                    next_node = trans.dst
                    break
            if not next_node:
                logger.debug("[ENGINE] workflow end")
                break
            current = next_node


class TransitionBuilder:
    """
    DSL Builder
    """

    def __init__(self, wf, src):
        self.wf = wf
        self.src = src
        self._condition = None
        self._name = None

    def on(self, result, name: Optional[str] = None):
        """匹配特定结果"""
        self._condition = lambda ctx: ctx.shared.last_result == result
        self._name = name or f"on({result})"
        return self

    def always(self, name: Optional[str] = None):
        """无条件转移"""
        self._condition = lambda ctx: True
        self._name = name or "always"
        return self

    def when(self, condition: Callable[[NodeContext], bool], name: Optional[str] = None):
        """自定义条件函数"""
        self._condition = condition
        self._name = name or "when()"
        return self

    def to(self, dst: str):
        """目标状态"""
        self.wf.add_transition(self.src, self._condition, dst, self._name)
        return self


class IWorkflow(ABC):

    @abstractmethod
    def execute(self, **kwargs):
        pass

# # =========================
# # 示例节点
# # =========================
#
# @node(retry=2)
# def detect(ctx: NodeContext):
#     logger.info("detect boss...")
#     if ctx.shared.fight_count < 3:
#         ctx.shared.boss_name = "Hecate"
#         return "found"
#     return "none"
#
#
# @node()
# def enter(ctx: NodeContext):
#     logger.info("enter instance")
#     return "ok"
#
#
# @node(timeout=5)
# def fight(ctx: NodeContext):
#     logger.info("fight boss")
#     ctx.shared.fight_count += 1
#     if ctx.shared.fight_count >= 3:
#         return "finish"
#     return "win"
#
#
# @node()
# def leave(ctx: NodeContext):
#     logger.info("leave instance")
#     return "done"
#
#
# if __name__ == '__main__':
#     # =========================
#     # 构建 Workflow
#     # =========================
#
#     wf = WorkflowEngine()
#
#     wf.source("detect").on("found").to("enter")
#     wf.source("detect").on("none").to("leave")
#
#     wf.source("enter").on("ok").to("fight")
#
#     wf.source("fight").on("win").to("detect")
#     wf.source("fight").on("finish").to("leave")
#
#     wf.source("leave").on("done").to(None)
#
#     (
#         wf.source("fight")
#         .when(lambda ctx: ctx.shared.fight_count >= 3).to(None)
#         .when(lambda ctx: ctx.shared.last_result == "win").to("wait")
#         .otherwise("start")
#     )
#
#     # =========================
#     # 运行
#     # =========================
#
#     ctx = NodeContext()
#
#     wf.run(ctx, "detect")
#
#     # =========================
#     # 统计输出
#     # =========================
#
#     logger.info("\n=== STATS ===")
#
#     logger.info("fight_count:", ctx.shared.fight_count)
#     logger.info("node_runs:", ctx.stats.node_runs)
#     logger.info("node_time:", ctx.stats.node_time)
#     logger.info("retries:", ctx.stats.retries)
#     logger.info("total_runtime:", time.time() - ctx.runtime.start_time)
