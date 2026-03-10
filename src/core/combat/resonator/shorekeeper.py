import logging
import time

import numpy as np

from src.core.combat.combat_core import ColorChecker, BaseResonator, CharClassEnum, ResonatorNameEnum
from src.core.exceptions import StopError
from src.core.interface import ControlService, ImgService

logger = logging.getLogger(__name__)


class BaseShorekeeper(BaseResonator):

    def __init__(self, control_service: ControlService, img_service: ImgService):
        super().__init__(control_service, img_service)

        # 协奏 左下血条旁黄圈
        self._concerto_energy_checker = ColorChecker.concerto_spectro()

        # 能量1 血条上方的5格能量
        self._energy1_point = [(547, 668), (548, 668), (552, 668)]
        self._energy1_color = [(114, 241, 255)]  # BGR
        self._energy1_checker = ColorChecker(self._energy1_point, self._energy1_color)

        # 能量2 血条上方的5格能量
        self._energy2_point = [(586, 668), (595, 668), (600, 668)]
        self._energy2_color = self._energy1_color
        self._energy2_checker = ColorChecker(self._energy2_point, self._energy2_color)

        # 能量3 血条上方的5格能量
        self._energy3_point = [(625, 668), (629, 668), (638, 668)]
        self._energy3_color = self._energy1_color
        self._energy3_checker = ColorChecker(self._energy3_point, self._energy3_color)

        # 能量4 血条上方的5格能量
        self._energy4_point = [(667, 668), (671, 668), (676, 668)]
        self._energy4_color = self._energy1_color
        self._energy4_checker = ColorChecker(self._energy4_point, self._energy4_color)

        # 能量5 血条上方的5格能量 两侧的蝴蝶
        self._energy5_point = [(701, 668), (710, 668), (714, 668)]
        self._energy5_color = self._energy1_color
        self._energy5_checker = ColorChecker(self._energy5_point, self._energy5_color)

        # 共鸣技能
        self._resonance_skill_point = [(1078, 630), (1078, 658), (1096, 655)]
        self._resonance_skill_color = [(255, 255, 255)]  # BGR
        self._resonance_skill_checker = ColorChecker(self._resonance_skill_point, self._resonance_skill_color)

        # 声骸技能
        self._echo_skill_point = [(1146, 633), (1152, 654), (1145, 658)]
        self._echo_skill_color = [(255, 255, 255)]  # BGR
        self._echo_skill_checker = ColorChecker(self._echo_skill_point, self._echo_skill_color)

        # 共鸣解放
        self._resonance_liberation_point = [(1211, 633), (1208, 653)]
        self._resonance_liberation_color = [(255, 255, 255)]  # BGR
        self._resonance_liberation_checker = ColorChecker(
            self._resonance_liberation_point, self._resonance_liberation_color)

    def __str__(self):
        return self.resonator_name().name

    def resonator_name(self) -> ResonatorNameEnum:
        return ResonatorNameEnum.shorekeeper

    def char_class(self) -> list[CharClassEnum]:
        return [CharClassEnum.Healer]

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
        if self._energy5_checker.check(img):
            energy_count = 5
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


class Shorekeeper(BaseShorekeeper):
    # COMBO_SEQ 为训练场单人静态完整连段，后续开发以此为准从中拆分截取

    # 常规轴
    COMBO_SEQ_0 = [
        # 3a E az
        ["a", 0.05, 0.31],
        ["a", 0.05, 0.43],
        ["a", 0.05, 0.40],
        ["E", 0.05, 0.32],
        ["a", 0.05, 0.35],
        # 清空能量
        ## 常规重击
        ["z", 0.50, 0.45],
        ## E跳a
        # ["E", 0.01, 0.05],
        # ["j", 0.05, 0.05],
        # ["a", 0.05, 0.00],
        # 间隔
        ["w", 0.00, 0.70],
        ["j", 0.05, 1.20],
    ]

    # 进阶轴
    COMBO_SEQ = [
        # 3a 四格能量
        ["a", 0.05, 0.31],
        ["a", 0.05, 0.43],
        ["a", 0.05, 0.40],
        # 进入蝴蝶 有连击则四格能量起手，无连击三格能量起手（重击会先a一下变四格能量）
        ["z", 0.50, 0.30],
        # 退出蝴蝶 五格能量
        ["a", 0.01, 0.01],
        ["E", 0.01, 0.10],
        # 清空能量
        ["j", 0.05, 0.15],
        ["a", 0.05, 0.10],
        ["Q", 0.05, 0.10],
        # 间隔
        ["w", 0.00, 0.35],
        # ["j", 0.05, 1.20],
        # 开大
        ["R", 0.05, 1.20],
    ]

    def __init__(self, control_service: ControlService, img_service: ImgService):
        super().__init__(control_service, img_service)

    def E(self):
        logger.debug("E")
        return [
            ["E", 0.05, 0.10],
        ]

    def zE(self):
        logger.debug("zE")
        return [
            ["z", 0.50, 0.30],
            ["E", 0.01, 0.10],
            ["a", 0.05, 0.05],  # 多一个普攻打断z防止一直飞
            ["a", 0.05, 0.05],  # 多一个普攻打断z防止一直飞
        ]

    def Eja(self):
        logger.debug("Eja")
        return [
            ["E", 0.01, 0.10],
            # 清空能量
            ["j", 0.05, 0.17],
            ["a", 0.05, 0.10],
        ]

    def ja(self):
        logger.debug("ja")
        return [
            # 清空能量
            ["j", 0.05, 0.05],
            ["a", 0.05, 0.05],
            ["w", 0.00, 0.17],
        ]

    def zaEja(self):
        logger.debug("zaEja")
        return [
            # 进入蝴蝶 有连击则四格能量起手，无连击三格能量起手（重击会先a一下变四格能量）
            ["z", 0.50, 0.30],
            # 退出蝴蝶 五格能量
            ["a", 0.01, 0.01],
            ["E", 0.01, 0.10],
            # 清空能量
            ["j", 0.05, 0.17],
            ["a", 0.05, 0.10],
            ["a", 0.05, 0.00],  # 多一个普攻
            # ["Q", 0.05, 0],
            # 间隔
            ["w", 0.00, 0.55],
        ]

    # def a3Eaz(self):
    #     logger.debug("a3Eaz")
    #     return [
    #         # 3a E az
    #         ["a", 0.05, 0.31],
    #         ["a", 0.05, 0.43],
    #         ["a", 0.05, 0.40],
    #         # ["E", 0.05, 0.32],
    #         ["E", 0.05, 0.00],
    #         ["a", 0.05, 0.32],
    #
    #         ["a", 0.05, 0.35],
    #         # 清空能量
    #         ## 常规重击
    #         # ["z", 0.50, 0.45],
    #         ["z", 0.50, 0.05],
    #         ["a", 0.05, 0.05],  # 多一个普攻打断z防止一直飞
    #         ["a", 0.05, 0.05],  # 多一个普攻打断z防止一直飞
    #     ]

    def a3Ea(self):
        logger.debug("a3Ea")
        return [
            # 3a E az
            ["a", 0.05, 0.31],
            # ["a", 0.05, 0.43],  # 拆分
            ["a", 0.05, 0.18],
            ["a", 0.05, 0.20],
            # ["a", 0.05, 0.40],  # 拆分
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.15],
            # ["E", 0.05, 0.32],
            ["E", 0.05, 0.00],
            ["a", 0.05, 0.32],  # E后接a，防止E没好原地发呆

            ["a", 0.05, 0.35],
        ]

    def a2(self):
        logger.debug("a2")
        return [
            # 2a
            ["a", 0.05, 0.31],
            # ["a", 0.05, 0.43],  # 拆分
            ["a", 0.05, 0.18],
            ["a", 0.05, 0.20],
        ]

    def a3(self):
        logger.debug("a3")
        return [
            # 3a
            ["a", 0.05, 0.31],
            # ["a", 0.05, 0.43],  # 拆分
            ["a", 0.05, 0.18],
            ["a", 0.05, 0.20],
            # ["a", 0.05, 0.40],  # 拆分
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.15],
        ]

    def za(self):
        logger.debug("za")
        return [
            # 清空能量
            ## 常规重击
            # ["z", 0.50, 0.45],
            ["z", 0.50, 0.05],
            ["a", 0.05, 0.05],  # 多一个普攻打断z防止一直飞
            ["a", 0.05, 0.05],  # 多一个普攻打断z防止一直飞
        ]

    def Q(self):
        logger.debug("Q")
        return [
            ["Q", 0.05, 0.10],
        ]

    def R(self):
        logger.debug("R")
        return [
            ["R", 0.05, 3.42],
        ]

    def full_combo(self):
        # 测试用，一整套连招
        # return self.COMBO_SEQ_0
        return self.COMBO_SEQ

    def combo(self):
        try:
            img = self.img_service.screenshot()
            # energy_count = self.energy_count(img)
            # is_concerto_energy_ready = self.is_concerto_energy_ready(img)
            # is_resonance_skill_ready = self.is_resonance_skill_ready(img)
            # is_echo_skill_ready = self.is_echo_skill_ready(img)
            is_resonance_liberation_ready = self.is_resonance_liberation_ready(img)
            # boss_hp = self.boss_hp(img)

            # 性价比a3
            self.combo_action(self.a3(), True)

            # 协星调律
            if is_resonance_liberation_ready:
                self.combo_action(self.E(), False)
                self.combo_action(self.R(), True)
                return

            ## 打满能量

            img = self.img_service.screenshot()
            energy_count = self.energy_count(img)
            is_resonance_skill_ready = self.is_resonance_skill_ready(img)
            is_resonance_liberation_ready = self.is_resonance_liberation_ready(img)
            boss_hp = self.boss_hp(img)

            if energy_count == 3 and is_resonance_skill_ready and boss_hp > 0.01:
                self.combo_action(self.zaEja(), False)
                self.combo_action(self.Q(), False)
                return

            self.combo_action(self.E(), not is_resonance_liberation_ready)
            self.combo_action(self.R(), is_resonance_liberation_ready)
            # 不打z，改成ja。防止击败boss时停卡掉按键，导致变成蝴蝶飞出场外
            if energy_count == 5:
                self.combo_action(self.ja(), False)

            self.combo_action(self.Q(), False)
        except StopError as e:
            self.control_service.jump()  # 打断守岸人变身蝴蝶
            raise e
