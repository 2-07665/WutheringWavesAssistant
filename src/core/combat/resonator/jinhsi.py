import logging
import time

import numpy as np

from src.core.combat.combat_core import ColorChecker, BaseResonator, CharClassEnum, LogicEnum, ResonatorNameEnum, \
    combat_cache
from src.core.interface import ControlService, ImgService

logger = logging.getLogger(__name__)


class BaseJinhsi(BaseResonator):

    def __init__(self, control_service: ControlService, img_service: ImgService):
        super().__init__(control_service, img_service)

        # 协奏 左下血条旁黄圈
        self._concerto_energy_checker = ColorChecker.concerto_spectro()

        # 共鸣技能 E1 流光夕影
        self._resonance_skill_point = [(1064, 650), (1077, 662)]
        self._resonance_skill_color = [(255, 255, 255)]  # BGR
        self._resonance_skill_checker = ColorChecker(
            self._resonance_skill_point, self._resonance_skill_color, logic=LogicEnum.AND)

        # 共鸣技能 E2 神霓飞芒 进入乘岁凌霄
        self._resonance_skill_2_point = [(1081, 635), (1086, 636), (1079, 649)]
        self._resonance_skill_2_color = [(255, 255, 255)]  # BGR
        self._resonance_skill_2_checker = ColorChecker(
            self._resonance_skill_2_point, self._resonance_skill_2_color, logic=LogicEnum.AND)

        # 共鸣技能 E2 神霓飞芒 入场黄色
        self._resonance_skill_2_incoming_color = [(173, 238, 249)]  # BGR
        self._resonance_skill_2_incoming_checker = ColorChecker(
            self._resonance_skill_2_point, self._resonance_skill_2_incoming_color, tolerance=50, logic=LogicEnum.AND)

        # 共鸣技能 E3 逐天取月
        self._resonance_skill_3_point = [(1082, 630), (1077, 634), (1085, 662)]
        self._resonance_skill_3_color = [(255, 255, 255)]  # BGR
        self._resonance_skill_3_checker = ColorChecker(
            self._resonance_skill_3_point, self._resonance_skill_3_color, logic=LogicEnum.AND)

        # 共鸣技能 E4 惊龙破空
        self._resonance_skill_4_point = [(1080, 641), (1086, 654), (1094, 652), (1085, 648)]
        self._resonance_skill_4_color = [(255, 255, 255)]  # BGR
        self._resonance_skill_4_checker = ColorChecker(
            self._resonance_skill_4_point, self._resonance_skill_4_color, logic=LogicEnum.AND)

        # 共鸣技能 E4 惊龙破空 入场黄色
        self._resonance_skill_4_incoming_color = [(173, 238, 249)]  # BGR
        self._resonance_skill_4_incoming_checker = ColorChecker(
            self._resonance_skill_4_point, self._resonance_skill_4_incoming_color, logic=LogicEnum.AND)

        # 声骸技能
        self._echo_skill_point = [(1146, 654), (1146, 657)]
        self._echo_skill_color = [(255, 255, 255)]  # BGR
        self._echo_skill_checker = ColorChecker(self._echo_skill_point, self._echo_skill_color)

        # 共鸣解放
        self._resonance_liberation_point = [(1208, 633), (1211, 660), (1224, 654)]
        self._resonance_liberation_color = [(255, 255, 255), (173, 238, 249)]  # BGR
        self._resonance_liberation_checker = ColorChecker(
            self._resonance_liberation_point, self._resonance_liberation_color)

    def __str__(self):
        return self.resonator_name().name

    def resonator_name(self) -> ResonatorNameEnum:
        return ResonatorNameEnum.jinhsi

    def char_class(self) -> list[CharClassEnum]:
        return [CharClassEnum.MainDPS]

    def is_concerto_energy_ready(self, img: np.ndarray) -> bool:
        is_ready = self._concerto_energy_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-协奏: {is_ready}")
        return is_ready

    def is_resonance_skill_ready(self, img: np.ndarray) -> bool:
        is_ready = self._resonance_skill_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-共鸣技能-流光夕影: {is_ready}")
        return is_ready

    def is_resonance_skill_2_ready(self, img: np.ndarray) -> bool:
        is_ready = self._resonance_skill_2_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-共鸣技能2-神霓飞芒: {is_ready}")
        return is_ready

    def is_resonance_skill_2_incoming_ready(self, img: np.ndarray) -> bool:
        is_ready = self._resonance_skill_2_incoming_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-共鸣技能2-神霓飞芒-入场: {is_ready}")
        return is_ready

    def is_resonance_skill_3_ready(self, img: np.ndarray) -> bool:
        is_ready = self._resonance_skill_3_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-共鸣技能3-逐天取月: {is_ready}")
        return is_ready

    def is_resonance_skill_4_ready(self, img: np.ndarray) -> bool:
        is_ready = self._resonance_skill_4_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-共鸣技能4-惊龙破空: {is_ready}")
        return is_ready

    def is_resonance_skill_4_incoming_ready(self, img: np.ndarray) -> bool:
        is_ready = self._resonance_skill_4_incoming_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-共鸣技能4-惊龙破空-入场: {is_ready}")
        return is_ready

    def is_echo_skill_ready(self, img: np.ndarray) -> bool:
        is_ready = self._echo_skill_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-声骸技能: {is_ready}")
        return is_ready

    def is_resonance_liberation_ready(self, img: np.ndarray) -> bool:
        is_ready = self._resonance_liberation_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-共鸣解放: {is_ready}")
        return is_ready


class Jinhsi(BaseJinhsi):
    # COMBO_SEQ 为训练场单人静态完整连段，后续开发以此为准从中拆分截取

    # 常规轴
    COMBO_SEQ_0 = [
        ["a", 0.05, 0.45],
        ["a", 0.05, 0.45],
        ["a", 0.05, 0.90],
        ["a", 0.05, 0.35],
        ["E", 0.05, 0.00],
        # 间隔
        ["w", 0.00, 0.75],  # 间隔(合轴点)需足够，否则二段开始，角色却还在一段的后摇中，会吞按键

        ["a", 0.05, 0.45],
        ["a", 0.05, 0.55],
        ["a", 0.05, 0.25],
        ["E", 0.05, 0.75],
        ["a", 0.05, 0.35],
        ["a", 0.05, 0.30],
        ["E", 0.05, 0.00],
    ]

    # 进阶轴
    # 速喷 BV1sUfHYdEPG
    COMBO_SEQ = [
        ["a", 0.05, 0.45],
        ["a", 0.05, 0.45],
        ["a", 0.05, 0.90],
        ["a", 0.05, 0.40],

        ["E", 0.05, 0.05],
        ["d", 0.05, 0.30],
        ["a", 0.05, 0.05],
        ["j", 0.05, 0.01],

        ["W_down", 0.00, 0.00],
        ["a", 0.05, 0.05],
        ["d", 0.05, 0.30],
        ["W_up", 0.00, 0.00],
        ["a", 0.05, 0.05],
        ["d", 0.05, 0.30],

        # # 直接喷 E4
        # ["a", 0.05, 0.05],
        # ["E", 0.05, 0.00],

        # 升龙再喷 E3E4
        ["E", 0.05, 1.00],
        ["a", 0.05, 0.20],
        ["a", 0.05, 0.20],
        ["E", 0.05, 0.00],

        ["w", 0.05, 2.50],
        # ["j", 0.05, 0.15],
    ]

    # 变奏速喷 BV1rS5Vz4Egy BV1dtEgzUEAF
    COMBO_SEQ_2 = [
        ["j", 0.002, 0.005],
        ["a", 0.002, 0.005],
        ["j", 0.002, 0.005],
        ["E", 0.002, 0.005],
    ]

    def __init__(self, control_service: ControlService, img_service: ImgService):
        super().__init__(control_service, img_service)

    @combat_cache
    def a4(self):
        """ 普攻打出E2 """
        return [
            ["a", 0.05, 0.45],
            ["a", 0.05, 0.45],

            # ["a", 0.05, 0.90],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.25],

            # ["a", 0.05, 0.35],
            ["a", 0.05, 0.10],  # 拆分
            ["a", 0.05, 0.00],  # 冗余多打一个普攻
            ["w", 0.00, 0.20],
        ]

    @combat_cache
    def a2(self):
        """ 普攻，变奏速喷前置动作，触发下发攻击 """
        return [
            ["a", 0.05, 0.10],
            ["a", 0.05, 0.10],
        ]

    @combat_cache
    def E2_full_combo_E4(self):
        """ E2起手的一整套 """
        # 这套容易触发闪避断招，伤害也偏低，但打的快
        return [
            ["E", 0.05, 0.05],
            ["d", 0.05, 0.30],
            ["a", 0.05, 0.05],
            ["j", 0.05, 0.01],

            ["W_down", 0.00, 0.00],
            ["a", 0.05, 0.05],
            ["d", 0.05, 0.30],
            ["W_up", 0.00, 0.00],
            ["a", 0.05, 0.05],
            ["d", 0.05, 0.30],

            # 直接喷 E4
            # ["a", 0.05, 0.05],
            # ["E", 0.05, 2.50],
            ["a", 0.05, 0.05],  # 多打一个aE，防止低帧率打不出喷
            ["E", 0.05, 0.30],
            ["a", 0.05, 0.05],
            ["E", 0.05, 2.05],

            # # 升龙再喷 E3E4
            # # ["E", 0.05, 1.00],  # 实战若被打断普攻次数不够会原地发呆，E后接普攻保证有事可做
            # ["E", 0.05, 0.10],
            # ["a", 0.05, 0.30],
            # # ["a", 0.05, 0.30],  # 提高a的点击频率，保证实战普攻次数覆盖
            # ["a", 0.05, 0.15],
            # ["a", 0.05, 0.15],
            # ["a", 0.05, 0.10],
            # ["E", 0.05, 0.10],
            #
            # ["a", 0.05, 0.20],
            # ["a", 0.05, 0.20],
            # ["a", 0.05, 0.10],  # 冗余多打一个普攻
            # ["E", 0.05, 0.10],
            # ["E", 0.05, 0.00],  # 冗余多打一个E
            #
            # ["w", 0.00, 2.50],
        ]

    @combat_cache
    def E2_full_combo_E3E4(self):
        """ E2起手的一整套 """
        # 这套不容易触发闪避，伤害高一些，但打的慢一些
        return [
            ["E", 0.05, 0.05],
            ["d", 0.05, 0.30],
            ["a", 0.05, 0.05],
            ["j", 0.05, 0.01],

            # ["W_down", 0.00, 0.00],
            ["a", 0.05, 0.05],
            ["d", 0.05, 0.30],
            # ["W_up", 0.00, 0.00],
            ["a", 0.05, 0.05],
            ["d", 0.05, 0.30],

            # # 直接喷 E4
            # ["a", 0.05, 0.05],
            # ["E", 0.05, 2.50],

            # 升龙再喷 E3E4
            # ["E", 0.05, 1.00],  # 实战若被打断普攻次数不够会原地发呆，E后接普攻保证有事可做
            ["E", 0.05, 0.25],
            ["E", 0.05, 0.20],
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.20],

            ["a", 0.05, 0.20],
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.10],  # 冗余多打一个普攻
            ["E", 0.05, 0.10],
            ["E", 0.05, 0.00],  # 冗余多打一个E

            ["w", 0.00, 2.50],
        ]

    @combat_cache
    def E2_intro_full_combo(self):
        """ E2 变奏速喷 120帧限定技 """
        return [
            ["j", 0.002, 0.005],
            ["a", 0.002, 0.005],
            ["j", 0.002, 0.005],
            ["E", 0.002, 0.005],
        ]

    @combat_cache
    def E3_full_combo(self):
        """ E3起手的一整套 """
        return [
            # ["a", 0.05, 0.45],  # 等待时间太长，拆分
            # ["a", 0.05, 0.55],
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.15],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.20],

            ["a", 0.05, 0.35],
            ["a", 0.05, 0.10],  # 冗余多打一个普攻

            # ["E", 0.05, 0.75],  # 实战若被打断普攻次数不够会原地发呆，E后接普攻保证有事可做
            ["E", 0.05, 0.10],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],
            ["E", 0.05, 0.00],

            ["a", 0.05, 0.35],
            ["a", 0.05, 0.35],
            ["a", 0.05, 0.20],  # 冗余多打一个普攻
            ["E", 0.05, 0.00],
            ["E", 0.05, 0.00],

            ["w", 0.00, 2.50],
        ]

    @combat_cache
    def E(self):
        """ 只打E，E4/E2使用 """
        return [
            # 变奏入场或在空中，容易出下落攻击，只打E
            ["E", 0.05, 0.10],
            ["E", 0.05, 0.10],
        ]

    @combat_cache
    def Q(self):
        return [
            # 声骸技能
            ["Q", 0.05, 0.00],
        ]

    @combat_cache
    def R(self):
        return [
            ["R", 0.05, 2.00],
        ]

    def full_combo(self):
        # 测试用，一整套连招
        return self.COMBO_SEQ

    def combo(self):

        img = self.img_service.screenshot()
        # is_concerto_energy_ready = self.is_concerto_energy_ready(img)
        is_resonance_skill_ready = self.is_resonance_skill_ready(img)
        is_resonance_skill_2_ready = self.is_resonance_skill_2_ready(img)
        is_resonance_skill_2_incoming_ready = self.is_resonance_skill_2_incoming_ready(img)
        is_resonance_skill_3_ready = self.is_resonance_skill_3_ready(img)
        is_resonance_skill_4_ready = self.is_resonance_skill_4_ready(img)
        is_resonance_skill_4_incoming_ready = self.is_resonance_skill_4_incoming_ready(img)
        # is_echo_skill_ready = self.is_echo_skill_ready(img)
        is_resonance_liberation_ready = self.is_resonance_liberation_ready(img)
        boss_hp = self.boss_hp(img)

        self.combo_action(self.Q(), False)

        if is_resonance_skill_2_ready or is_resonance_skill_2_incoming_ready:
            # self.combo_action(self.a2(), True)
            # _E2_intro_full_combo = self.E2_intro_full_combo()
            # for i in range(50):
            #     self.combo_action(_E2_intro_full_combo, True)

            time.sleep(0.5)
            self.combo_action(self.E(), False)
            time.sleep(0.5)
            self.combo_action(self.E(), False)
            return

        if is_resonance_skill_4_ready or is_resonance_skill_4_incoming_ready:
            self.combo_action(self.E(), False)
            self.combo_action(self.R(), False)  # 冗余
            return

        if is_resonance_liberation_ready:
            self.combo_action(self.R(), False)
            self.combo_action(self.E(), False)  # 冗余
            return

        if is_resonance_skill_3_ready:
            self.combo_action(self.E3_full_combo(), False)
            return

        # E1作为共鸣技能是否CD的指标
        if is_resonance_skill_ready:
            self.combo_action(self.a4(), False)
            img = self.img_service.screenshot()
            is_resonance_skill_2_ready = self.is_resonance_skill_2_ready(img)
            if is_resonance_skill_2_ready:
                if boss_hp <= 0.2:
                    _E2_full_combo = self.E2_full_combo_E4()
                else:
                    _E2_full_combo = self.E2_full_combo_E4() if self.random_float() < 0.5 else self.E2_full_combo_E3E4()
                self.combo_action(_E2_full_combo, False)
                time.sleep(0.05)
            else:
                self.combo_action(self.E(), False)
                self.combo_action(self.R(), False)
                time.sleep(0.05)
            return

        # 兜底，共鸣技能还没好，随便打几下
        self.combo_action(self.a4(), False)
        img = self.img_service.screenshot()
        is_resonance_skill_4_ready = self.is_resonance_skill_4_ready(img)
        is_resonance_skill_2_ready = self.is_resonance_skill_2_ready(img)
        if is_resonance_skill_4_ready or is_resonance_skill_2_ready:
            self.combo_action(self.E(), False)
            time.sleep(0.05)
        self.combo_action(self.R(), False)
