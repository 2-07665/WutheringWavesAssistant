import logging
import time

import numpy as np

from src.core.combat.combat_core import ColorChecker, BaseResonator, CharClassEnum, LogicEnum, \
    ResonatorNameEnum, combat_cache
from src.core.interface import ControlService, ImgService

logger = logging.getLogger(__name__)


class BaseSanhua(BaseResonator):

    def __init__(self, control_service: ControlService, img_service: ImgService):
        super().__init__(control_service, img_service)

        # 协奏 左下血条旁黄圈
        self._concerto_energy_checker = ColorChecker.concerto_glacio()

        # 共鸣技能
        self._resonance_skill_point = [(1082, 631), (1080, 659)]
        self._resonance_skill_color = [(255, 255, 255)]  # BGR
        self._resonance_skill_checker = ColorChecker(
            self._resonance_skill_point, self._resonance_skill_color, logic=LogicEnum.AND)

        # 声骸技能
        self._echo_skill_point = [(1140, 654), (1146, 652)]
        self._echo_skill_color = [(255, 255, 255)]  # BGR
        self._echo_skill_checker = ColorChecker(self._echo_skill_point, self._echo_skill_color)

        # 共鸣解放
        self._resonance_liberation_point = [(1206, 654)]
        self._resonance_liberation_color = [(255, 255, 255), (255, 193, 142), (255, 193, 142), (255, 214, 181)]  # BGR
        self._resonance_liberation_checker = ColorChecker(
            self._resonance_liberation_point, self._resonance_liberation_color)

    def __str__(self):
        return self.resonator_name().name

    def resonator_name(self) -> ResonatorNameEnum:
        return ResonatorNameEnum.sanhua

    def char_class(self) -> list[CharClassEnum]:
        return [CharClassEnum.Support]

    def is_concerto_energy_ready(self, img: np.ndarray) -> bool:
        is_ready = self._concerto_energy_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-协奏: {is_ready}")
        return is_ready

    def is_resonance_skill_ready(self, img: np.ndarray) -> bool:
        is_ready = self._resonance_skill_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-共鸣技能: {is_ready}")
        return is_ready

    def is_echo_skill_ready(self, img: np.ndarray) -> bool:
        is_ready = self._echo_skill_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-声骸技能: {is_ready}")
        return is_ready

    def is_resonance_liberation_ready(self, img: np.ndarray) -> bool:
        is_ready = self._resonance_liberation_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-共鸣解放: {is_ready}")
        return is_ready


class Sanhua(BaseSanhua):
    # COMBO_SEQ 为训练场单人静态完整连段，后续开发以此为准从中拆分截取

    # 常规轴
    COMBO_SEQ = [
        # 普攻4a
        ["a", 0.05, 0.36],
        ["a", 0.05, 0.33],
        ["a", 0.05, 0.60],
        ["a", 0.05, 0.67],
        ["a", 0.05, 0.89],
        ["j", 0.05, 1.20],

        # # 重击爆裂
        # ["z", 0.915, 1.30],
        # ["j", 0.05, 1.20],

        ["w", 0.00, 1.00],

        # Ez
        ["E", 0.05, 0.20],
        ["z", 0.85, 1.56],
        ["j", 0.05, 1.20],

        # 辉萤军势
        ["Q", 0.05, 0.66],
        ["a", 0.05, 0.93],
        ["a", 0.05, 1.23],
        ["j", 0.05, 1.20],

        # # 无常凶鹭
        # ["Q", 0.05, 1.45],
        # ["j", 0.05, 1.20],

        # 普攻4a
        ["a", 0.05, 0.36],
        ["a", 0.05, 0.33],
        ["a", 0.05, 0.60],
        ["a", 0.05, 0.67],
        ["a", 0.05, 0.89],
        ["j", 0.05, 1.20],

        # ERz
        ["E", 0.05, 0.39],
        ["R", 0.05, 0.05],
        ["z", 1.85, 1.43],
        ["j", 0.05, 1.20],

        # 下落攻击
        ["j", 0.05, 0.28],
        ["a", 0.05, 0.75],
        ["j", 0.05, 1.20],

    ]

    def __init__(self, control_service: ControlService, img_service: ImgService):
        super().__init__(control_service, img_service)

    @combat_cache
    def a3(self):
        return [
            # 普攻 随便打几下
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.35],
            ["a", 0.05, 0.35],
        ]

    @combat_cache
    def z(self):
        return [
            ["z", 0.915, 1.30],
        ]

    @combat_cache
    def Ez(self):
        return [
            # Ez
            ["E", 0.05, 0.20],
            ["z", 0.85, 1.56],
        ]

    @combat_cache
    def Rz(self):
        return [
            ["R", 0.05, 0.05],
            ["z", 1.85, 1.43],
        ]

    @combat_cache
    def ERz(self):
        return [
            # ERz
            ["E", 0.05, 0.39],
            ["R", 0.05, 0.05],
            # ["z", 1.85, 1.43],
            ["z", 1.90, 1.43],  # 稍微按久一点
        ]

    @combat_cache
    def Q(self):
        return [
            # 声骸技能
            ["Q", 0.05, 1.45],
        ]

    @combat_cache
    def EQ(self):
        return [
            ["E", 0.05, 0.39],
            ["Q", 0.05, 1.45],
        ]

    def full_combo(self):
        # 测试用，一整套连招
        return self.COMBO_SEQ

    def combo(self):
        # 变奏下砸
        self.combo_action(self.a3(), True)

        img = self.img_service.screenshot()
        # is_concerto_energy_ready = self.is_concerto_energy_ready(img)
        is_resonance_skill_ready = self.is_resonance_skill_ready(img)
        is_echo_skill_ready = self.is_echo_skill_ready(img)
        is_resonance_liberation_ready = self.is_resonance_liberation_ready(img)

        # 大红莲华
        if is_resonance_liberation_ready:
            if is_resonance_skill_ready:
                self.combo_action(self.ERz(), False)
            else:
                self.combo_action(self.Rz(), False)
            time.sleep(0.05)
            return

        # E
        if is_resonance_skill_ready:
            if is_echo_skill_ready:
                self.combo_action(self.EQ(), False)
            else:
                self.combo_action(self.Ez(), False)
                time.sleep(0.05)
            return

        # Q
        if is_echo_skill_ready:
            self.combo_action(self.Q(), False)
            return

        # 兜底
        self.combo_action(self.a3(), False)
