import logging
import time

import numpy as np

from src.core.combat.combat_core import ColorChecker, BaseResonator, CharClassEnum, LogicEnum, ResonatorNameEnum, \
    combat_cache
from src.core.interface import ControlService, ImgService

logger = logging.getLogger(__name__)


class BaseEncore(BaseResonator):

    def __init__(self, control_service: ControlService, img_service: ImgService):
        super().__init__(control_service, img_service)

        # 协奏 左下血条旁红圈
        self._concerto_energy_checker = ColorChecker.concerto_fusion()

        # 能量满 血条上方的能量
        self._energy_full_point = [(723, 667), (724, 668)]
        self._energy_full_color = [(97, 121, 255)]  # BGR
        self._energy_full_checker = ColorChecker(self._energy_full_point, self._energy_full_color)

        # 共鸣技能
        self._resonance_skill_point = [(1074, 635), (1091, 634), (1082, 658)]
        self._resonance_skill_color = [(255, 255, 255)]  # BGR
        self._resonance_skill_checker = ColorChecker(self._resonance_skill_point, self._resonance_skill_color)

        # 声骸技能
        self._echo_skill_point = [(1146, 632), (1141, 652), (1160, 656)]
        self._echo_skill_color = [(255, 255, 255)]  # BGR
        self._echo_skill_checker = ColorChecker(self._echo_skill_point, self._echo_skill_color)

        # 共鸣解放
        self._resonance_liberation_point = [(1202, 657), (1219, 656)]
        self._resonance_liberation_color = [(255, 255, 255)]  # BGR
        self._resonance_liberation_checker = ColorChecker(
            self._resonance_liberation_point, self._resonance_liberation_color)

        # 共鸣解放 黑咩大暴走状态
        self._cosmos_rave_point = [(532, 673), (734, 673)]
        self._cosmos_rave_color = [(73, 81, 181)]  # BGR
        self._cosmos_rave_checker = ColorChecker(
            self._cosmos_rave_point, self._cosmos_rave_color, logic=LogicEnum.AND)

    def __str__(self):
        return self.resonator_name().name

    def resonator_name(self) -> ResonatorNameEnum:
        return ResonatorNameEnum.encore

    def char_class(self) -> list[CharClassEnum]:
        return [CharClassEnum.MainDPS]

    def energy_count(self, img: np.ndarray) -> int:
        # 安可只看能量是否满，满为1，未满为0
        energy_count = 0
        if self._energy_full_checker.check(img):
            energy_count = 1
            logger.debug(f"{self.resonator_name().value}-能量: 已满")
        else:
            logger.debug(f"{self.resonator_name().value}-能量: 未满")
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

    def is_cosmos_rave_ready(self, img: np.ndarray) -> bool:
        is_ready = self._cosmos_rave_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-黑咩大暴走状态: {is_ready}")
        return is_ready


class Encore(BaseEncore):
    # COMBO_SEQ 为训练场单人静态完整连段，后续开发以此为准从中拆分截取

    # 常规轴
    COMBO_SEQ = [
        # ja
        ["j", 0.05, 0.33],
        ["a", 0.05, 0.72],
        ["j", 0.05, 1.20],

        # Ea
        ["E", 0.05, 1.90],
        ["a", 0.05, 0.90],
        ["j", 0.05, 1.20],

        # 普攻5a
        ["a", 0.05, 0.30],
        ["a", 0.05, 0.40],
        ["a", 0.05, 0.52],
        ["a", 0.05, 0.62],
        ["a", 0.05, 1.22],
        ["j", 0.05, 1.20],

        # R
        ["R", 0.05, 2.63],
        ["j", 0.05, 1.20],

        # R E普攻E，普攻连点打满一套的时间
        ["E", 0.05, 0.28],
        ["a", 0.05, 0.30],
        ["a", 0.05, 0.30],
        ["a", 0.05, 0.30],
        ["a", 0.05, 0.30],
        ["a", 0.05, 0.30],
        ["a", 0.05, 0.30],
        ["a", 0.05, 0.30],
        ["a", 0.05, 0.30],
        ["a", 0.05, 0.30],
        ["a", 0.05, 0.30],
        ["a", 0.05, 0.30],
        ["E", 0.05, 0.28],
        ["w", 0.05, 1.20],
        ["j", 0.05, 1.20],
    ]

    def __init__(self, control_service: ControlService, img_service: ImgService):
        super().__init__(control_service, img_service)

    @combat_cache
    def E(self):
        return [
            # E
            ["E", 0.05, 1.90],
        ]

    @combat_cache
    def Ea(self):
        return [
            # Ea
            # ["E", 0.05, 1.90],  # 等待时间太长，实战容易发呆，拆分
            ["E", 0.05, 0.00],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.15],
            ["a", 0.05, 0.05],

            # ["a", 0.05, 0.90],  # 拆分，增加频率保证打出派生
            ["a", 0.05, 0.15],
            ["a", 0.05, 0.15],
            ["a", 0.05, 0.15],
            ["a", 0.05, 0.15],
            ["a", 0.05, 0.15],
        ]

    @combat_cache
    def a5(self):
        return [
            # 普攻5a
            # ["a", 0.05, 0.30],
            # ["a", 0.05, 0.40],
            # ["a", 0.05, 0.52],
            # ["a", 0.05, 0.62],
            # ["a", 0.05, 1.22],

            ["a", 0.05, 0.30],

            ["a", 0.05, 0.15],  # 普攻间隔太长，拆分
            ["a", 0.05, 0.15],

            ["a", 0.05, 0.20],
            ["a", 0.05, 0.22],

            ["a", 0.05, 0.25],
            ["a", 0.05, 0.27],

            ["a", 0.05, 1.22],
        ]

    @combat_cache
    def a3(self):
        return [
            # 3a，固定频率连点数下，用于脱离空中状态，非普攻连段
            # ["a", 0.05, 0.30],  # 拆分
            ["a", 0.05, 0.15],
            ["a", 0.05, 0.15],
            # ["a", 0.05, 0.30],  # 拆分
            ["a", 0.05, 0.15],
            ["a", 0.05, 0.15],

            ["a", 0.05, 0.30]
        ]

    # def a2(self):
    #     logger.debug("a2")
    #     return [
    #         # ja的时间轴，用于打变奏下落攻击
    #         ["a", 0.05, 0.32],
    #         ["a", 0.05, 0.40],
    #     ]

    @combat_cache
    def a2(self):
        return [
            # 普攻5a的后两下
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.22],

            ["a", 0.05, 0.25],
            ["a", 0.05, 0.27],

            ["a", 0.05, 1.22],
        ]

    @combat_cache
    def R(self):
        return [
            # R
            ["R", 0.05, 2.63],
        ]

    @combat_cache
    def Ea11E(self):
        return [
            # R E普攻E，普攻连点打满一套的时间
            ["E", 0.05, 0.28],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],
            # ["E", 0.05, 0.28],  # 拆分多打几下E
            ["E", 0.05, 0.10],
            ["E", 0.05, 0.10],
            ["w", 0.00, 0.08],
        ]

    @combat_cache
    def z(self):
        return [
            # 重击
            ["z", 0.70, 3.00],
        ]

    @combat_cache
    def Qa3(self):
        return [
            # 声骸技能，梦魇摩托
            ["Q", 0.05, 0.30],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.10],  # 多a一下
            ["a", 0.05, 1.60],
        ]

    @combat_cache
    def Q(self):
        return [
            # 声骸技能，普通摩托
            ["Q", 0.05, 0.30],
        ]

    def full_combo(self):
        # 测试用，一整套连招
        return self.COMBO_SEQ

    def combo(self):

        time.sleep(0.1)
        self.combo_action(self.a3(), True)  # 入场先打几个普攻，触发下落攻击

        img = self.img_service.screenshot()
        energy_count = self.energy_count(img)
        # is_concerto_energy_ready = self.is_concerto_energy_ready(img)
        is_resonance_skill_ready = self.is_resonance_skill_ready(img)
        is_echo_skill_ready = self.is_echo_skill_ready(img)
        is_resonance_liberation_ready = self.is_resonance_liberation_ready(img)
        is_cosmos_rave_ready = self.is_cosmos_rave_ready(img)

        # 黑咩大暴走状态
        if is_cosmos_rave_ready:
            self.combo_action(self.Ea11E(), False)
            return

        # 别靠近安可
        if energy_count == 1:
            self.combo_action(self.z(), False)
            return

        # 开大，空中放不出R
        if is_resonance_liberation_ready:
            # self.combo_action(self.a3(), True)
            # time.sleep(0.2)
            self.combo_action(self.R(), True)
            # time.sleep(0.2)
            # img = self.img_service.screenshot()
            # is_cosmos_rave_ready = self.is_cosmos_rave_ready(img)
            # if is_cosmos_rave_ready:
            self.combo_action(self.Ea11E(), True)
            img = self.img_service.screenshot()
            energy_count = self.energy_count(img)
            if energy_count == 1:
                self.combo_action(self.z(), False)
            return

        # 呼呼啦开
        if is_resonance_skill_ready:
            if self.random_float() < 0.66:
                self.combo_action(self.Ea(), False)
            else:
                # self.combo_action(self.a3(), False)
                self.combo_action(self.E(), False)
            time.sleep(0.05)
            return

        if is_echo_skill_ready:
            self._random_echo_skill()
            self.combo_action(self.E(), False)
            return

        # 兜底，打一套普攻
        self.combo_action(self.a2(), is_echo_skill_ready)

        # 大招图标在切人时会先红一下，导致颜色无法匹配，最后再匹配一次
        img = self.img_service.screenshot()
        is_resonance_liberation_ready = self.is_resonance_liberation_ready(img)
        if is_resonance_liberation_ready:
            self.combo_action(self.R(), True)
            time.sleep(0.2)
            img = self.img_service.screenshot()
            is_cosmos_rave_ready = self.is_cosmos_rave_ready(img)
            if is_cosmos_rave_ready:
                self.combo_action(self.Ea11E(), True)
                img = self.img_service.screenshot()
                energy_count = self.energy_count(img)
                if energy_count == 1:
                    self.combo_action(self.z(), False)
            return

        # 摩托最后放合轴
        if is_echo_skill_ready:
            self._random_echo_skill()
        else:
            self.combo_action(self.E(), False)

    def _random_echo_skill(self):
        # 随机放梦魇摩托或普通摩托
        random_q = self.Qa3() if self.random_float() < 0.5 else self.Q()
        self.combo_action(random_q, False)
