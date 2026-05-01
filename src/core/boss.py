import logging
from enum import Enum

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class BossNameEnum(Enum):
    Dreamless = "无妄者"
    FallacyOfNoReturn = "无归的谬误"
    LampylumenMyriad = "辉萤军势"
    BellBorneGeochelone = "鸣钟之龟"
    InfernoRider = "燎照之骑"
    ImpermanenceHeron = "无常凶鹭"
    MechAbomination = "聚械机偶"
    MourningAix = "哀声鸷"
    ThunderingMephis = "朔雷之鳞"
    TempestMephis = "云闪之鳞"
    FeilianBeringal = "飞廉之猩"
    Crownless = "无冠者"
    Jue = "角"
    SentryConstruct = "异构武装"
    Hecate = "赫卡忒"
    Lorelei = "罗蕾莱"
    DragonOfDirge = "叹息古龙"
    NightmareFeilianBeringal = "梦魇飞廉之猩"
    NightmareImpermanenceHeron = "梦魇无常凶鹭"
    NightmareTempestMephis = "梦魇云闪之鳞"
    NightmareThunderingMephis = "梦魇朔雷之鳞"
    NightmareCrownless = "梦魇无冠者"
    NightmareInfernoRider = "梦魇燎照之骑"
    NightmareMourningAix = "梦魇哀声鸷"
    NightmareLampylumenMyriad = "梦魇辉萤军势"
    Fleurdelys = "芙露德莉斯"
    NightmareKelpie = "梦魇凯尔匹"
    LionessOfGlory = "荣耀狮像"
    NightmareHecate = "梦魇赫卡忒"
    Fenrico = "芬莱克"
    LadyOfTheSea = "海之女"
    TheFalseSovereign = "伪作的神王"
    ThrenodianLeviathan = "鸣式利维亚坦"
    Hyvatia = "海维夏"
    ReactorHusk = "炉芯机骸"
    Sigillum = "辛吉勒姆"
    NamelessExplorer = "无铭探索者"
    SeedOfLllusoryOrigin = "虚妄诞生之种（限时提前开放）"
    Denia = "达妮娅"


class MoveMode(Enum):
    WALK = "walk"  # 适合短距离
    RUN = "run"  # 适合长距离


class Direction(Enum):
    LEFT = "left"
    RIGHT = "right"
    FORWARD = "forward"
    BACKWARD = "backward"

    @staticmethod
    def get_key(direction: "Direction"):
        if direction == Direction.LEFT:
            return "a"
        elif direction == Direction.RIGHT:
            return "d"
        elif direction == Direction.BACKWARD:
            return "s"
        return "w"

class RouteStep(BaseModel):
    """
    用于定义角色传送到boss后，如何走到boss前，如何到重新挑战处
    """

    direction: Direction
    mode: MoveMode
    steps: int | None = Field(
        default=None,
        description="走动步数"
    )
    duration: float | None = Field(
        default=None,
        description="跑动时间，秒"
    )


_DEFAULT_RESTART_TEXT = r"^(重新挑战|Restart)$"


class RestartParam(BaseModel):
    """
    通用的参数配置，用于以下逻辑

    前置场景：传送到boss后，执行跑向boss，此时离boss还有一定距离（特意这样设计的，为了兼容不同角色的移速）
    此时要做的：
    """
    # 1、先原地查找boss相关的关键字（仅部分boss有击败等字样）
    check_text: str | None = Field(None, description="检查文本，None为不检查")
    # 2、若有可确定boss存在，直接跑完剩余的距离，到boss跟前即可
    direction: Direction | None = Field(None, description="移动方向，默认向前")
    # 3、若原地找不到1中的关键字 或 没有可识别的关键字，则按重新挑战来，循环前进查找"重新挑战"文本
    cycle: int | None = Field(None, description="循环次数")
    step: int | None = Field(None, description="循环中每次前进步数")
    check_health_bar: bool = Field(default=False, description="循环中每次检测boss血条，用于没有文本可识别的boss，通过血条判断是否存在")
    restart_text: str | None = Field(default=_DEFAULT_RESTART_TEXT, description="循环中识别的重新挑战等文本")