import logging
import multiprocessing
import threading
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class MsgType(Enum):
    LOG = auto()
    TASK_STATUS = auto()
    ERROR = auto()
    STATS = auto()
    EVENT = auto()


class MsgTaskStatus(Enum):
    PENDING = auto()
    RUNNING = auto()
    SUCCESS = auto()
    FAILED = auto()
    CANCELLED = auto()


class MsgSource(Enum):
    SCREENSHOT = auto()
    WINDOW = auto()
    INPUT = auto()
    TASK = auto()
    SYSTEM = auto()
    WORKFLOW = auto()

    DAILY_TASK = auto()


@dataclass
class Message:
    type: MsgType
    source: MsgSource
    data: Dict[str, Any] = field(default_factory=dict)
    task_id: Optional[str] = None
    msg_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    ts: float = field(default_factory=time.time)


class MessageBus:
    """ 消息总线 """

    def __init__(self):
        self._handlers = []
        self._lock = threading.Lock()

    def subscribe(
            self,
            handler: Callable,
            msg_type: Optional[MsgType] = None,
            source: Optional[MsgSource] = None,
    ):
        """ 注册订阅 """
        with self._lock:
            self._handlers.append((handler, msg_type, source))

    def publish(self, msg: Message):
        with self._lock:
            handlers = list(self._handlers)

        for handler, mtype, src in handlers:
            if mtype and msg.type != mtype:
                continue
            if src and msg.source != src:
                continue

            try:
                handler(msg)
            except Exception:
                logger.exception("[MessageBus] handler error")


class ProcessBridge:
    """ 跨进程桥接 """

    def __init__(self, bus: MessageBus):
        self.queue = multiprocessing.Queue()
        self.bus = bus
        self._running = False

    def start(self):
        self._running = True
        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        while self._running:
            try:
                msg = self.queue.get()
                self.bus.publish(msg)
            except Exception:
                logger.exception("[ProcessBridge] handler error")


def make_sender(queue_or_bus, source: MsgSource, task_id: str):
    """ 构建任务消息发送器 """

    def send(msg_type: MsgType, **data):
        msg = Message(
            type=msg_type,
            source=source,
            data=data,
            task_id=task_id,
        )

        # 自动适配 queue 或 bus
        if hasattr(queue_or_bus, "put"):
            queue_or_bus.put(msg)
        else:
            queue_or_bus.publish(msg)

    return send


