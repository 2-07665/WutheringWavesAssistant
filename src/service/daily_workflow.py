import inspect
import logging
import re
import time
from dataclasses import dataclass
from typing import Optional

from src.core.boss import RouteStep, Direction, MoveMode
from src.core.geometry import AnchorBBox, Align, AnchorPoint, PointKind
from src.core.message import MsgType, MsgTaskStatus
from src.core.pages import I18nPage, I18nText, UIOp
from src.core.task import TaskFSM, TaskStatus
from src.core.workflow import node, WorkflowEngine, NodeContext, IWorkflow

logger = logging.getLogger(__name__)


@dataclass
class TaskLocal:
    # guidebook
    activityFSM: Optional[TaskFSM] = None
    materialsSpotsFSM: Optional[TaskFSM] = None
    recurringChallengesFSM: Optional[TaskFSM] = None
    pathOfGrowthFSM: Optional[TaskFSM] = None
    enemyTracingFSM: Optional[TaskFSM] = None
    milestonesFSM: Optional[TaskFSM] = None

    ## ------- Guidebook MaterialsSpots -------
    forgeryChallengeFSM: Optional[TaskFSM] = None
    simulationChallengeFSM: Optional[TaskFSM] = None
    bossChallengeFSM: Optional[TaskFSM] = None
    tacetSuppressionFSM: Optional[TaskFSM] = None
    weeklyChallengeFSM: Optional[TaskFSM] = None
    nightmarePurificationFSM: Optional[TaskFSM] = None
    tacetDiscordNestFSM: Optional[TaskFSM] = None

    ### ------- Guidebook MaterialsSpots tacetDiscordNest -------
    starblindCrashsiteTacetDiscordNestFSM: Optional[TaskFSM] = None
    rebirthUplandsTacetDiscordNestFSM: Optional[TaskFSM] = None
    stagnantRunTacetDiscordNestFSM: Optional[TaskFSM] = None

    isAllCompleteFSM: Optional[TaskFSM] = None


class NodeName:
    navigateToValidPage = "navigateToValidPage"
    navigateToGuidebook = "navigateToGuidebook"

    doActivity = "doActivity"
    doMaterialsSpots = "doMaterialsSpots"
    doRecurringChallenges = "doRecurringChallenges"
    doPathOfGrowth = "doPathOfGrowth"
    doEnemyTracing = "doEnemyTracing"
    doMilestones = "doMilestones"

    doCombat = "doCombat"

    isAllComplete = "isAllComplete"
    endNode = "endNode"


@node(NodeName.endNode)
def endNode(ctx: NodeContext, **kwargs) -> bool:
    logger.debug(inspect.currentframe().f_code.co_name)
    ctx.runtime.taskFSM.complete()
    ctx.runtime.send(MsgType.TASK_STATUS, status=MsgTaskStatus.SUCCESS)
    time.sleep(0.1)
    return True


@node(NodeName.navigateToValidPage)
def navigateToValidPage(ctx: NodeContext, **kwargs) -> Optional[str]:
    # 检查是否在有效页面（如 终端），不在则esc尝试离开（如 在副本内）
    logger.debug(inspect.currentframe().f_code.co_name)

    # 已在终端页
    ui = UIOp(ctx)
    if ui.snapshot().is_match(I18nPage.UI_ESC_Terminal.PAGE):
        logger.debug("已在终端")
        return I18nPage.UI_ESC_Terminal.PAGE

    # 在全局预设中找出离开函数，尝试回到主页
    if ctx.page_service.global_page_action(ui.oq.results):
        logger.debug("找到全局页面")
        time.sleep(1)
        return None

    # 兜底规则，esc
    logger.debug("未找到任何页面")
    ui.esc().sleep(1)
    return None


@node(NodeName.navigateToGuidebook)
def navigateToGuidebook(ctx: NodeContext, local: TaskLocal, **kwargs) -> Optional[str]:
    # 索拉指南
    logger.debug(inspect.currentframe().f_code.co_name)
    ui = UIOp(ctx)
    ui.activate().sleep(0.1)

    # 终端
    if ui.snapshot().is_match(I18nPage.UI_ESC_Terminal.PAGE):
        # 点击进入索拉指南
        guidebook = ctx.tr(I18nText.Guidebook)
        guidebook_bbox = ctx.scaler.as_bbox(  # 取右侧区域，防止被左侧昵称、签名等影响
            AnchorBBox(AnchorPoint(500, 0, Align.Top | Align.Left), AnchorPoint(1280, 720, Align.Right | Align.Bottom)))
        if not ui.click_text(guidebook, guidebook_bbox):
            logger.warning(f"Text not found: {guidebook}")
            return None
        ui.sleep(0.8)

    # 左侧图标坐标
    activitySidebar = AnchorPoint(50, 117, Align.Top | Align.Left)
    materialsSpotsSidebar = AnchorPoint(50, 208, Align.Top | Align.Left)
    recurringChallengesSidebar = AnchorPoint(50, 300, Align.Top | Align.Left)
    pathOfGrowthSidebar = AnchorPoint(50, 385, Align.Top | Align.Left)
    enemyTracingSidebar = [
        AnchorPoint(50, 475, Align.Top | Align.Left),
        AnchorPoint(50, 565, Align.Top | Align.Left),
        AnchorPoint(50, 385, Align.Top | Align.Left),
    ]
    milestonesSidebar = AnchorPoint(50, 564, Align.Top | Align.Left)

    # 进入索拉指南后，默认是 活跃度 或 素材获取 页
    activity = ctx.tr(I18nText.Activity)
    materialsSpots = ctx.tr(I18nText.MaterialsSpots)
    recurringChallenges = ctx.tr(I18nText.RecurringChallenges)
    pathOfGrowth = ctx.tr(I18nText.PathOfGrowth)
    enemyTracing = ctx.tr(I18nText.EnemyTracing)
    milestones = ctx.tr(I18nText.Milestones)

    title = [activity, materialsSpots, recurringChallenges, pathOfGrowth, enemyTracing, milestones]
    title_roi = ctx.scaler.as_bbox(
        AnchorBBox(AnchorPoint(0, 0, Align.Top | Align.Left), AnchorPoint(300, 100, Align.Top | Align.Left)))

    sub_ui = UIOp(ctx, ctx.guidebook_service)
    result = sub_ui.wait(5, 0.3).until(lambda: sub_ui.snapshot().search(title, title_roi))
    if not result:
        logger.warning(f"Text not found: {activity} / {materialsSpots}")
        return None

    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"activityFSM.is_active: {local.activityFSM.status.is_active}")
        logger.debug(f"materialsSpotsFSM.is_active: {local.materialsSpotsFSM.status.is_active}")
        logger.debug(f"recurringChallengesFSM.is_active: {local.recurringChallengesFSM.status.is_active}")
        logger.debug(f"pathOfGrowthFSM.is_active: {local.pathOfGrowthFSM.status.is_active}")
        logger.debug(f"enemyTracingFSM.is_active: {local.enemyTracingFSM.status.is_active}")
        logger.debug(f"milestonesFSM.is_active: {local.milestonesFSM.status.is_active}")

    if local.activityFSM.status.is_active:
        # 进来是活跃度页，代表每日活跃度没做完
        if sub_ui.search(activity, title_roi):
            return I18nText.Activity
        local.activityFSM.complete()
    elif local.materialsSpotsFSM.status.is_active:
        # 残像聚落 产出声骸套件
        if not sub_ui.search(materialsSpots, title_roi):
            sub_ui.click_point(materialsSpotsSidebar, 2, 0.2).sleep(0.3)

        if local.forgeryChallengeFSM.status.is_active:
            return I18nText.ForgeryChallenge
        if local.simulationChallengeFSM.status.is_active:
            return I18nText.SimulationChallenge
        if local.bossChallengeFSM.status.is_active:
            return I18nText.BossChallenge
        if local.tacetSuppressionFSM.status.is_active:
            return I18nText.TacetSuppression
        if local.weeklyChallengeFSM.status.is_active:
            return I18nText.WeeklyChallenge
        if local.nightmarePurificationFSM.status.is_active:
            return I18nText.NightmarePurification
        if local.tacetDiscordNestFSM.status.is_active:
            return I18nText.TacetDiscordNest

        local.materialsSpotsFSM.complete()
    elif local.recurringChallengesFSM.status.is_active:
        # 周期挑战
        return I18nText.RecurringChallenges
    elif local.pathOfGrowthFSM.status.is_active:

        return I18nText.PathOfGrowth
    elif local.enemyTracingFSM.status.is_active:

        return I18nText.EnemyTracing
    elif local.milestonesFSM.status.is_active:

        return I18nText.Milestones

    return None


@node(NodeName.doMaterialsSpots)
def doMaterialsSpots(ctx: NodeContext, local: TaskLocal, **kwargs) -> bool:
    if local.tacetDiscordNestFSM.status.is_terminal:
        return True
    sub_ui = UIOp(ctx, ctx.guidebook_service)
    tacets = [
        I18nText.StarblindCrashsiteTacetDiscordNest,
        I18nText.RebirthUplandsTacetDiscordNest,
        I18nText.StagnantRunTacetDiscordNest,
    ]
    tacets_fsm = [
        local.starblindCrashsiteTacetDiscordNestFSM,
        local.rebirthUplandsTacetDiscordNestFSM,
        local.stagnantRunTacetDiscordNestFSM,
    ]
    cur_tacet_idx = 0
    # cur_tacet_idx = -1
    # for index, fsm in enumerate(tacets_fsm):
    #     if fsm.status.is_active:
    #         cur_tacet_idx = index
    #         break
    # if cur_tacet_idx < 0:
    #     return True
    try:
        # 点击残像聚落
        sub_ui.snapshot().click_text(ctx.tr(I18nText.TacetDiscordNest), pk=PointKind.RANDOM)
        sub_ui.sleep(0.3)
        tacets_group = tacets + [I18nText.Go, I18nText.TacetDiscordDefeated]
        # 获取聚落列表
        tacets_tbox = sub_ui.snapshot().search([ctx.tr(i) for i in tacets_group])
        tacets_tbox.sort(key=lambda p: p.y1)
        while cur_tacet_idx < len(tacets):
            # if cur_tacet_idx + 2 > len(tacets) - 1:
            #     # 滚轮
            #     pass

            # 检查击败数量
            sub_idx = cur_tacet_idx * 3
            go = tacets_tbox[sub_idx + 1]
            tacetDiscordDefeated = tacets_tbox[sub_idx + 2]
            match = re.search(r"(\d{1,2}).*?(\d{1,2})", tacetDiscordDefeated.text)
            logger.debug(f"match: {match}")
            if int(match.group(1)) >= int(match.group(2)):
                cur_tacet_idx += 1
                continue

            # 点击前往
            result = sub_ui.click_bbox(go).sleep(1).wait(5, 0.3).until(
                lambda: sub_ui.snapshot().search(ctx.tr(I18nText.FastTravel)))
            if not result:
                return False
            # 点击快速旅行
            sub_ui.click_bbox(result[0], times=2, interval=0.3)
            sub_ui.sleep(3).wait_back_home().sleep(1.5)
            # 前往战斗区域
            test_route = [
                RouteStep(direction=Direction.RIGHT, mode=MoveMode.RUN, duration=0.5),
                RouteStep(direction=Direction.FORWARD, mode=MoveMode.RUN, duration=4.0),
            ]
            sub_ui.execute_route(test_route)

            # combat_system = ctx.combat_service.combat_system()
            from src.core.combat.combat_system import CombatSystem
            combat_system = CombatSystem(ctx.control_service, ctx.img_service)
            combat_system.resonators = [combat_system.cartethyia, None, None]
            combat_system.is_async = True

            timeout = 10 * 60
            deadline = time.monotonic() + timeout
            while ctx.runtime.stop_event.is_set() or time.monotonic() < deadline:
                combat_system.start(3.5)
                sub_ui.sleep(1.5).snapshot()
                # 残象聚落已清理
                if sub_ui.search(ctx.tr(I18nText.ClearTheTacetDiscordNest)):
                    combat_system.stop()
                    sub_ui.sleep(0.3)
                    continue
                # 清理聚落中的残象
                if sub_ui.search(ctx.tr(I18nText.TacetDiscordNestCleared)):
                    break

            # 吸收
            ctx.control_service.pick_up()
            tacets_fsm[cur_tacet_idx].complete()
        local.tacetDiscordNestFSM.complete()
    except Exception as e:
        logger.exception(e)
        tacets_fsm[cur_tacet_idx].fail()
    local.tacetDiscordNestFSM.fail()
    return False


@node(NodeName.doCombat)
def doCombat(ctx: NodeContext, local: TaskLocal, **kwargs) -> bool:
    pass


@node(NodeName.isAllComplete)
def isAllComplete(ctx: NodeContext, local: TaskLocal, **kwargs) -> bool:
    # 检查任务完成情况，决定是否结束
    all_fsm = [
        local.activityFSM,
        local.materialsSpotsFSM,
        local.recurringChallengesFSM,
        local.pathOfGrowthFSM,
        local.enemyTracingFSM,
        local.milestonesFSM,
    ]
    for fsm in all_fsm:
        if fsm.status.is_active:
            return False
    local.isAllCompleteFSM.complete()
    return True


class DailyWorkflow(IWorkflow):

    def __init__(self, ctx: NodeContext):
        self.ctx: NodeContext = ctx
        self.engine = WorkflowEngine()
        self.fsm = TaskFSM.build(self.ctx)
        self.local = TaskLocal()

        self.__init_workflow()
        self.__init_task_local()

    def __init_workflow(self):
        (
            self.engine.source(NodeName.navigateToValidPage, is_start=True)
            .on(I18nPage.UI_ESC_Terminal.PAGE).to(NodeName.navigateToGuidebook)
            .always().to(NodeName.navigateToValidPage)  # TODO 加循环次数限制
        )

        (
            self.engine.source(NodeName.navigateToGuidebook)
            .on(I18nText.Activity).to(NodeName.doActivity)
            .on(I18nText.MaterialsSpots).to(NodeName.doMaterialsSpots)
            .on(I18nText.RecurringChallenges).to(NodeName.doRecurringChallenges)
            .on(I18nText.PathOfGrowth).to(NodeName.doPathOfGrowth)
            .on(I18nText.EnemyTracing).to(NodeName.doEnemyTracing)
            .on(I18nText.Milestones).to(NodeName.doMilestones)
            .always().to(NodeName.isAllComplete)
        )

        self.engine.source(NodeName.doActivity).always().to(NodeName.isAllComplete)
        self.engine.source(NodeName.doMaterialsSpots).always().to(NodeName.isAllComplete)
        self.engine.source(NodeName.doRecurringChallenges).always().to(NodeName.isAllComplete)
        self.engine.source(NodeName.doPathOfGrowth).always().to(NodeName.isAllComplete)
        self.engine.source(NodeName.doEnemyTracing).always().to(NodeName.isAllComplete)
        self.engine.source(NodeName.doMilestones).always().to(NodeName.isAllComplete)

        (
            self.engine.source(NodeName.isAllComplete)
            .when(lambda ctx: not ctx.shared.last_result).to(NodeName.navigateToValidPage)
            .always().to(NodeName.endNode)
        )

    def __init_task_local(self):
        # TODO 根据配置设置

        self.local.activityFSM = TaskFSM.build(self.ctx, TaskStatus.NOT_REQUIRED)
        self.local.materialsSpotsFSM = TaskFSM.build(self.ctx, TaskStatus.PENDING)
        self.local.recurringChallengesFSM = TaskFSM.build(self.ctx, TaskStatus.NOT_REQUIRED)
        self.local.pathOfGrowthFSM = TaskFSM.build(self.ctx, TaskStatus.NOT_REQUIRED)
        self.local.enemyTracingFSM = TaskFSM.build(self.ctx, TaskStatus.NOT_REQUIRED)
        self.local.milestonesFSM = TaskFSM.build(self.ctx, TaskStatus.NOT_REQUIRED)
        self.local.tacetDiscordNestFSM = TaskFSM.build(self.ctx, TaskStatus.PENDING)
        self.local.starblindCrashsiteTacetDiscordNestFSM = TaskFSM.build(self.ctx, TaskStatus.PENDING)
        self.local.rebirthUplandsTacetDiscordNestFSM = TaskFSM.build(self.ctx, TaskStatus.PENDING)
        self.local.stagnantRunTacetDiscordNestFSM = TaskFSM.build(self.ctx, TaskStatus.PENDING)

    def execute(self, **kwargs):
        try:
            logger.debug(f"task: {self.__class__.__name__}")
            self.ctx.runtime.taskFSM = self.fsm
            self.fsm.start()
            self.ctx.control_service.activate()
            time.sleep(0.1)
            self.engine.run(self.ctx, self, local=self.local, **kwargs)
        except Exception as e:
            self.fsm.fail()
            raise e
