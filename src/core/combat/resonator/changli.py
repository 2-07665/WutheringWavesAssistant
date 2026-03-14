import logging
import time

import numpy as np

from src.core.combat.combat_core import ColorChecker, BaseResonator, CharClassEnum, ResonatorNameEnum, combat_cache
from src.core.interface import ControlService, ImgService

logger = logging.getLogger(__name__)


class BaseChangli(BaseResonator):

    def __init__(self, control_service: ControlService, img_service: ImgService):
        super().__init__(control_service, img_service)

        # 协奏 左下血条旁红圈
        self._concerto_energy_checker = ColorChecker.concerto_fusion()

        # 能量1 血条上方的4格能量
        self._energy1_point = [(547, 668), (548, 668), (552, 668)]
        self._energy1_color = [(107, 97, 250)]  # BGR
        self._energy1_checker = ColorChecker(self._energy1_point, self._energy1_color)

        # 能量2 血条上方的4格能量
        self._energy2_point = [(595, 668), (604, 668), (614, 668)]
        self._energy2_color = self._energy1_color
        self._energy2_checker = ColorChecker(self._energy2_point, self._energy2_color)

        # 能量3 血条上方的4格能量
        self._energy3_point = [(649, 668), (659, 668), (668, 668)]
        self._energy3_color = self._energy1_color
        self._energy3_checker = ColorChecker(self._energy3_point, self._energy3_color)

        # 能量4 血条上方的4格能量
        self._energy4_point = [(692, 668), (701, 668), (711, 668)]
        self._energy4_color = self._energy1_color
        self._energy4_checker = ColorChecker(self._energy4_point, self._energy4_color)

        # 共鸣技能
        self._resonance_skill_point = [(1071, 634), (1093, 631), (1082, 662)]
        self._resonance_skill_color = [(255, 255, 255)]  # BGR
        self._resonance_skill_checker = ColorChecker(self._resonance_skill_point, self._resonance_skill_color)

        # 声骸技能
        self._echo_skill_point = [(1146, 632), (1141, 652), (1160, 656)]
        self._echo_skill_color = [(255, 255, 255)]  # BGR
        self._echo_skill_checker = ColorChecker(self._echo_skill_point, self._echo_skill_color)

        # 共鸣解放
        self._resonance_liberation_point = [(1207, 653), (1213, 652)]
        self._resonance_liberation_color = [(255, 255, 255)]  # BGR
        self._resonance_liberation_checker = ColorChecker(
            self._resonance_liberation_point, self._resonance_liberation_color)

    def __str__(self):
        return self.resonator_name().name

    def resonator_name(self) -> ResonatorNameEnum:
        return ResonatorNameEnum.changli

    def char_class(self) -> list[CharClassEnum]:
        return [CharClassEnum.SubDPS]

    def energy_count(self, img: np.ndarray) -> int:
        energy_count = 0
        if self._energy1_checker.check(img):
            energy_count = 1
        if self._energy2_checker.check(img):
            energy_count = 2
        if self._energy3_checker.check(img):
            energy_count = 3
        if self._energy4_checker.check(img):
            energy_count = 4
        logger.debug(f"{self.resonator_name().value}-能量: {energy_count}格")
        return energy_count

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


class Changli(BaseChangli):
    # COMBO_SEQ 为训练场单人静态完整连段，后续开发以此为准从中拆分截取

    # 常规轴
    COMBO_SEQ = [
        # 声骸技能
        ["Q", 0.05, 0.30],
        ["a", 0.05, 0.30],
        ["a", 0.05, 0.30],
        ["a", 0.05, 1.60],
        ["j", 0.05, 1.20],
        # 共鸣技能 Ea 一离火
        ["E", 0.05, 1.25],
        ["a", 0.05, 1.30],
        # ["E", 0.05, 1.25],
        # ["a", 0.05, 1.30],
        # 间隔
        ["w", 0.00, 1.20],
        # 普攻 5a 一离火
        ["a", 0.05, 0.31],
        ["a", 0.05, 0.50],
        ["a", 0.05, 0.50],
        ["a", 0.05, 1.05],
        ["a", 0.05, 0.00],
        ["w", 0.05, 0.75],
        ["j", 0.05, 1.2],
        # 共鸣技能 Ea 一离火
        ["E", 0.05, 1.25],
        ["a", 0.05, 1.30],
        ["w", 0.00, 1.20],
        # 普攻 5a 一离火
        ["a", 0.05, 0.31],
        ["a", 0.05, 0.50],
        ["a", 0.05, 0.50],
        ["a", 0.05, 1.05],
        ["a", 0.05, 0.00],
        ["w", 0.05, 0.75],
        ["j", 0.05, 1.20],
        # zRz
        ["z", 0.50, 0.90],
        ["R", 0.05, 1.65],
        ["z", 1.90, 0.00],
        ["w", 0.00, 1.00],
        ["j", 0.05, 0.00],
    ]

    def __init__(self, control_service: ControlService, img_service: ImgService):
        super().__init__(control_service, img_service)

    @combat_cache
    def Ea(self):
        return [
            # 共鸣技能 Ea 一离火
            # ["E", 0.05, 1.25],
            # ["a", 0.05, 1.30],

            ["E", 0.05, 0.30],  # 冗余
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],

            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.40],
            ["a", 0.05, 0.30],
        ]

    @combat_cache
    def E(self):
        return [
            # 共鸣技能 E
            ["E", 0.05, 1.25],
        ]

    @combat_cache
    def a2(self):
        return [
            # 普攻 2a
            ["a", 0.05, 0.31],
            # ["a", 0.05, 0.50],
            ["a", 0.05, 0.30],
        ]

    # def a5(self):
    #     logger.debug("a5")
    #     return [
    #         # 普攻 5a 一离火
    #         ["a", 0.05, 0.31],
    #         ["a", 0.05, 0.50],
    #         ["a", 0.05, 0.50],
    #
    #         # ["a", 0.05, 1.05],
    #         ["a", 0.05, 0.35],
    #         ["a", 0.05, 0.35],
    #         ["a", 0.05, 0.20],
    #         ["a", 0.05, 0.10],
    #
    #         ["a", 0.05, 0.00],
    #         ["w", 0.05, 0.75],
    #     ]

    @combat_cache
    def a3(self):
        return [
            # 普攻 5a 一离火
            # ["a", 0.05, 0.31],
            # ["a", 0.05, 0.50],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.20],

            # ["a", 0.05, 1.05],
            ["a", 0.05, 0.35],
            ["a", 0.05, 0.35],
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.10],

            ["a", 0.05, 0.00],
            ["w", 0.05, 0.75],
        ]

    @combat_cache
    def a(self):
        return [
            ["a", 0.05, 0.31],
        ]

    # def zRz(self):
    #     return [
    #         # zRz 实战效果不好，若被打断等情况，会长时间原地发呆
    #         ["z", 0.60, 0.90],
    #         ["R", 0.05, 1.65],
    #         ["z", 1.90, 1.00],
    #     ]

    @combat_cache
    def Rz(self):
        return [
            # Rz
            ["R", 0.05, 1.65],
            ["z", 2.00, 1.00],
        ]

    @combat_cache
    def zR(self):
        return [
            # zR
            # ["z", 0.60, 1.10],
            # ["R", 0.05, 1.65],

            ["z", 0.60, 0.00],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.10],

            ["R", 0.05, 1.65],
        ]

    @combat_cache
    def z(self):
        return [
            # z
            ["z", 0.70, 1.10],
        ]

    @combat_cache
    def az(self):
        return [
            # az
            ["a", 0.05, 0.31],
            ["z", 0.70, 1.10],
        ]

    @combat_cache
    def Qa3(self):
        return [
            # 声骸技能，梦魇摩托
            ["Q", 0.05, 0.30],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],
            ["a", 0.05, 1.60],
        ]

    @combat_cache
    def Q(self):
        return [
            # 声骸技能，普通摩托
            ["Q", 0.05, 0.30],
        ]

    @combat_cache
    def R(self):
        return [
            ["R", 0.05, 1.65],
        ]

    def full_combo(self):
        # 测试用，一整套连招
        return self.COMBO_SEQ

    def combo(self):

        time.sleep(0.1)
        self.combo_action(self.a2(), False)  # 入场先打两个普攻，触发心眼冲
        time.sleep(0.2)

        img = self.img_service.screenshot()
        energy_count = self.energy_count(img)

        # 4离火 z
        if energy_count == 4:
            self.combo_action(self.z(), False)
            time.sleep(0.3)
            self.combo_action(self.a2(), False)  # 凑够0.9秒后摇时间
            time.sleep(0.3)
            # 空中重击会变成下落攻击，再次确认
            img = self.img_service.screenshot()
            energy_count = self.energy_count(img)
            if energy_count == 4:
                self.combo_action(self.z(), False)
                time.sleep(0.4)
                img = self.img_service.screenshot()
                energy_count = self.energy_count(img)
                if energy_count != 4:
                    time.sleep(0.6)
                    self.combo_action(self.Rz(), False)
            else:
                self.combo_action(self.E(), False)
            return

        # is_concerto_energy_ready = self.is_concerto_energy_ready(img)
        is_resonance_skill_ready = self.is_resonance_skill_ready(img)
        is_echo_skill_ready = self.is_echo_skill_ready(img)
        is_resonance_liberation_ready = self.is_resonance_liberation_ready(img)

        # 3离火，打满离火
        if energy_count == 3 and is_resonance_skill_ready:
            self.combo_action(self.Ea(), True)
            img = self.img_service.screenshot()
            energy_count = self.energy_count(img)
            is_resonance_liberation_ready = self.is_resonance_liberation_ready(img)
            if energy_count == 4:
                self.combo_action(self.z(), False)
                img = self.img_service.screenshot()
                is_resonance_liberation_ready = self.is_resonance_liberation_ready(img)
                if is_resonance_liberation_ready:
                    time.sleep(0.9)
                    self.combo_action(self.Rz(), False)
            elif is_resonance_liberation_ready:
                self.combo_action(self.Rz(), False)
            return

        # 低离火有大直接开
        if energy_count < 3 and is_resonance_liberation_ready:
            self.combo_action(self.Rz(), False)
            return

        # 兜底，打E合轴或普攻
        if is_resonance_skill_ready:
            self.combo_action(self.E(), is_echo_skill_ready)
        else:
            self.combo_action(self.a3(), False)
            time.sleep(0.3)
            img = self.img_service.screenshot()
            energy_count = self.energy_count(img)
            if energy_count == 4:
                self.combo_action(self.z(), False)
                return
            self.combo_action(self.a(), False)
        # 摩托最后放合轴
        if is_echo_skill_ready:
            # 随机放梦魇摩托或普通摩托
            # random_q = self.Qa3() if self.random_float() < 0.33 else self.Q()
            # self.combo_action(random_q, False)
            self.combo_action(self.Q(), False)
