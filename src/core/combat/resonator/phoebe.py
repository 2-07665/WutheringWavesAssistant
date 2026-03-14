import logging

import numpy as np

from src.core.combat.combat_core import ColorChecker, BaseResonator, CharClassEnum, LogicEnum, ResonatorNameEnum, \
    combat_cache
from src.core.interface import ControlService, ImgService

logger = logging.getLogger(__name__)


class BasePhoebe(BaseResonator):

    def __init__(self, control_service: ControlService, img_service: ImgService):
        super().__init__(control_service, img_service)

        # 协奏 左下血条旁黄圈
        self._concerto_energy_checker = ColorChecker.concerto_spectro()

        # 祈愿 未选择形态时 选择后位置会变
        self._prayer_base_form_point = [(547, 668), (593, 668), (653, 668), (712, 668)]
        self._prayer_base_form_color = [(148, 213, 250), (144, 185, 217)]  # BGR
        self._prayer_base_form_checker = ColorChecker(
            self._prayer_base_form_point, self._prayer_base_form_color, logic=LogicEnum.AND)

        # 祈愿 选择形态后
        self._prayer_shifted_form_point = [(721, 675)]
        self._prayer_shifted_form_color = [(114, 200, 251), (123, 201, 249), (152, 203, 219), (180, 207, 216)]  # BGR
        self._prayer_shifted_form_checker = ColorChecker(self._prayer_shifted_form_point,
                                                         self._prayer_shifted_form_color)

        # # 福音01
        # self._divine_voice_15_point = [(545, 668)]
        # self._divine_voice_15_color = [(196, 213, 220), (199, 200, 206), (176, 252, 255)]  # BGR
        # self._divine_voice_15_checker = ColorChecker(self._divine_voice_15_point, self._divine_voice_15_color)

        # 福音15
        self._divine_voice_15_point = [(576, 668), (577, 668), (581, 668)]
        self._divine_voice_15_color = [(190, 254, 255), (179, 253, 255), (203, 230, 240)]  # BGR
        self._divine_voice_15_checker = ColorChecker(self._divine_voice_15_point, self._divine_voice_15_color)

        # 福音30
        self._divine_voice_30_point = [(617, 668), (621, 668), (622, 668)]
        self._divine_voice_30_color = self._divine_voice_15_color
        self._divine_voice_30_checker = ColorChecker(self._divine_voice_30_point, self._divine_voice_30_color)

        # 赦罪 福音条中间 黄色为输出形态
        self._absolution_enhancement_point = [(633, 672), (634, 672)]
        self._absolution_enhancement_color = [(175, 234, 248)]  # BGR
        self._absolution_enhancement_checker = ColorChecker(
            self._absolution_enhancement_point, self._absolution_enhancement_color, logic=LogicEnum.AND)

        # 告解 福音条中间 蓝白色为辅助形态
        self._confession_enhancement_point = [(633, 672), (634, 672)]
        self._confession_enhancement_color = [(255, 255, 253)]  # BGR
        self._confession_enhancement_checker = ColorChecker(
            self._confession_enhancement_point, self._confession_enhancement_color, logic=LogicEnum.AND)

        # 共鸣技能 E1
        self._resonance_skill_point = [(1057, 637), (1071, 637)]
        self._resonance_skill_color = [(255, 255, 255)]  # BGR
        self._resonance_skill_checker = ColorChecker(
            self._resonance_skill_point, self._resonance_skill_color, logic=LogicEnum.AND)

        # 共鸣技能 E2
        self._resonance_skill_2_point = [(1063, 644), (1065, 644), (1064, 645), (1066, 645)]
        self._resonance_skill_2_color = [(255, 255, 255)]  # BGR
        self._resonance_skill_2_checker = ColorChecker(
            self._resonance_skill_2_point, self._resonance_skill_2_color, logic=LogicEnum.AND)

        # 声骸技能
        self._echo_skill_point = [(1134, 653), (1137, 653)]
        self._echo_skill_color = [(255, 255, 255)]  # BGR
        self._echo_skill_checker = ColorChecker(self._echo_skill_point, self._echo_skill_color)

        # 共鸣解放
        self._resonance_liberation_point = [(1201, 631), (1212, 631), (1199, 660)]
        self._resonance_liberation_color = [(255, 255, 255)]  # BGR
        self._resonance_liberation_checker = ColorChecker(
            self._resonance_liberation_point, self._resonance_liberation_color)

    def __str__(self):
        return self.resonator_name().name

    def resonator_name(self) -> ResonatorNameEnum:
        return ResonatorNameEnum.phoebe

    def char_class(self) -> list[CharClassEnum]:
        return [CharClassEnum.Support]

    def divine_voice(self, img: np.ndarray) -> int:
        divine_voice = 0
        if self._divine_voice_15_checker.check(img):
            divine_voice = 15
        if self._divine_voice_30_checker.check(img):
            divine_voice = 30
        if divine_voice == 30:
            logger.debug(f"{self.resonator_name().value}-福音: >={divine_voice}")
        else:
            logger.debug(f"{self.resonator_name().value}-福音: {divine_voice}")
        return divine_voice

    def is_absolution_enhancement(self, img: np.ndarray) -> bool:
        is_ready = self._absolution_enhancement_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-赦罪: {is_ready}")
        return is_ready

    def is_confession_enhancement(self, img: np.ndarray) -> bool:
        is_ready = self._confession_enhancement_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-告解: {is_ready}")
        return is_ready

    def is_concerto_energy_ready(self, img: np.ndarray) -> bool:
        is_ready = self._concerto_energy_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-协奏: {is_ready}")
        return is_ready

    def is_resonance_skill_ready(self, img: np.ndarray) -> bool:
        is_ready = self._resonance_skill_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-共鸣技能E1: {is_ready}")
        return is_ready

    def is_resonance_skill_2_ready(self, img: np.ndarray) -> bool:
        is_ready = self._resonance_skill_2_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-共鸣技能E2: {is_ready}")
        return is_ready

    def is_echo_skill_ready(self, img: np.ndarray) -> bool:
        is_ready = self._echo_skill_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-声骸技能: {is_ready}")
        return is_ready

    def is_resonance_liberation_ready(self, img: np.ndarray) -> bool:
        is_ready = self._resonance_liberation_checker.check(img)
        logger.debug(f"{self.resonator_name().value}-共鸣解放: {is_ready}")
        return is_ready


class Phoebe(BasePhoebe):
    # COMBO_SEQ 为训练场单人静态完整连段，后续开发以此为准从中拆分截取

    # 常规轴
    COMBO_SEQ = [
        # 普攻4a
        ["a", 0.05, 0.24],
        ["a", 0.05, 0.88],
        ["a", 0.05, 0.85],
        ["a", 0.05, 1.30],
        ["j", 0.05, 1.20],

        # 普攻4a取消
        ["a", 0.05, 0.24],
        ["a", 0.05, 0.88],
        ["a", 0.05, 0.85],
        ["a", 0.05, 0.10],
        ["d", 0.05, 0.30],
        ["j", 0.05, 1.20],

        # E3a E后从普攻第二段开始打 E加一层风蚀
        ["E", 0.05, 0.50],
        ["a", 0.05, 0.88],
        ["a", 0.05, 0.85],
        ["a", 0.05, 1.30],
        ["j", 0.05, 1.20],

        # jaaa
        ["j", 0.05, 0.12],
        ["a", 0.05, 0.65],
        ["a", 0.05, 0.78],
        ["a", 0.05, 1.20],
        ["j", 0.05, 1.20],

        # jaaa取消
        ["j", 0.05, 0.12],
        ["a", 0.05, 0.65],
        ["a", 0.05, 0.78],
        ["a", 0.05, 0.10],
        ["d", 0.05, 1.00],
        ["j", 0.05, 1.20],

        # 3能量 重击 加一层风蚀
        ["z", 1.54, 0.20],
        ["j", 0.05, 1.20],

        # 能量不满 重击上挑
        ["z", 0.82, 0.05],
        ["a", 0.05, 0.65],
        ["a", 0.05, 0.78],
        ["a", 0.05, 1.20],
        ["j", 0.05, 1.20],

        # 空中E 3音律重击
        ["j", 0.05, 0.12],
        ["E", 0.05, 0.15],
        ["z", 1.30, 0.40],
        ["j", 0.05, 1.20],

        # R 风蚀
        ["R", 0.05, 3.67],
        # ["1", 0.05, 1.20],

        # R 光噪
        ["R", 0.05, 3.67],
        ["A", 0.05, 0.30],
        ["A", 0.05, 0.15],
        # ["1", 0.05, 1.20],

        # R 全程
        ["R", 0.05, 3.67],  # 37950
        ["w", 0.00, 34.28],
        ["j", 0.05, 1.20],

        # jaaaEaaa
        ["j", 0.05, 0.12],
        ["a", 0.05, 0.65],
        ["a", 0.05, 0.78],
        ["a", 0.05, 0.10],
        ["E", 0.05, 0.50],
        ["a", 0.05, 0.65],
        ["a", 0.05, 0.78],
        ["a", 0.05, 0.10],
        ["j", 0.05, 1.20],

        # jEaaajaaa BV1N8KyzAENt
        ["j", 0.05, 0.12],
        ["E", 0.05, 0.50],
        ["a", 0.05, 0.65],
        ["a", 0.05, 0.78],
        ["a", 0.05, 0.10],
        ["j", 0.05, 0.12],
        ["a", 0.05, 0.65],
        ["a", 0.05, 0.78],
        ["a", 0.05, 0.10],
        ["j", 0.05, 1.20],

        # 枪系通用 瞄准加特林
        ["G", 0.008, 0.008],

        ["a", 0.008, 0.010],
        ["G", 0.008, 0.008],
        ["G", 0.008, 0.008],
        ["a", 0.008, 0.010],
        ["G", 0.008, 0.008],
        ["G", 0.008, 0.008],
        ["a", 0.008, 0.010],
        ["G", 0.008, 0.008],
        ["G", 0.008, 0.008],
        ["a", 0.008, 0.010],
        ["G", 0.008, 0.008],
        ["G", 0.008, 0.008],
        ["a", 0.008, 0.010],
        ["G", 0.008, 0.008],
        ["G", 0.008, 0.008],
        ["a", 0.008, 0.010],
        ["G", 0.008, 0.008],
        ["G", 0.008, 0.008],
        ["a", 0.008, 0.010],
        ["G", 0.008, 0.008],
        ["G", 0.008, 0.008],
        ["a", 0.008, 0.010],
        ["G", 0.008, 0.008],
        ["G", 0.008, 0.008],
        ["a", 0.008, 0.010],
        ["G", 0.008, 0.008],
        ["G", 0.008, 0.008],
        ["a", 0.008, 0.010],
        ["G", 0.008, 0.008],
        ["G", 0.008, 0.008],
        ["a", 0.008, 0.010],
        ["G", 0.008, 0.008],
        ["G", 0.008, 0.008],

        ["G", 0.008, 0.008],

        ["w", 0.00, 0.50],

        # 普攻 瞄准无限戳
        ["a", 0.008, 0.200],
        ["G", 0.008, 0.008],
        ["G", 0.008, 0.008],
        ["a", 0.008, 0.200],
        ["G", 0.008, 0.008],
        ["G", 0.008, 0.008],
        ["a", 0.008, 0.200],
        ["G", 0.008, 0.008],
        ["G", 0.008, 0.008],
        ["a", 0.008, 0.200],
        ["G", 0.008, 0.008],
        ["G", 0.008, 0.008],
        ["a", 0.008, 0.200],
        ["G", 0.008, 0.008],
        ["G", 0.008, 0.008],
        ["a", 0.008, 0.200],
        ["G", 0.008, 0.008],
        ["G", 0.008, 0.008],
        ["a", 0.008, 0.200],
        ["G", 0.008, 0.008],
        ["G", 0.008, 0.008],
    ]

    def __init__(self, control_service: ControlService, img_service: ImgService):
        super().__init__(control_service, img_service)

    @combat_cache
    def a4(self):
        return [
            # 普攻4a
            ["a", 0.05, 0.24],

            # ["a", 0.05, 0.88],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.28],

            # ["a", 0.05, 0.85],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.25],

            # ["a", 0.05, 1.30],
            ["a", 0.05, 0.15],
            ["a", 0.05, 0.10],
            ["w", 0.00, 1.00],
        ]

    @combat_cache
    def a_intro(self):
        return [
            # 普攻1.3秒，覆盖变奏时间
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.20],
            ["a", 0.05, 0.20],
        ]

    @combat_cache
    def a2_end(self):
        return [
            # 普攻4a的后两段
            # ["a", 0.05, 0.24],
            # ["a", 0.05, 0.88],

            # ["a", 0.05, 0.85],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.25],

            # ["a", 0.05, 1.30],
            ["a", 0.05, 0.15],
            ["a", 0.05, 0.10],
            ["w", 0.00, 1.00],
        ]

    # def z(self):
    #     logger.debug("z")
    #     return [
    #         # 能量不满 重击上挑
    #         ["z", 0.82, 0.05],
    #     ]

    @combat_cache
    def z_musical_essence_3(self):
        return [
            # 3能量 重击 加一层风蚀
            ["z", 1.54, 0.20],
        ]

    @combat_cache
    def E(self):
        return [
            # ["E", 0.05, 0.60],
            ["E", 0.05, 0.15],
            ["E", 0.05, 0.40],
        ]

    @combat_cache
    def E3a(self):
        return [
            # E3a E后从普攻第二段开始打 E加一层风蚀
            # ["E", 0.05, 0.50],
            ["E", 0.05, 0.15],
            ["E", 0.05, 0.30],

            # ["a", 0.05, 0.88],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.28],

            # ["a", 0.05, 0.85],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.25],

            # ["a", 0.05, 1.30],
            ["a", 0.05, 0.15],
            ["a", 0.05, 0.10],
            ["w", 0.00, 1.00],
        ]

    @combat_cache
    def jEz(self):
        return [
            # 空中E 3音律重击
            ["j", 0.05, 0.12],
            ["E", 0.05, 0.15],
            ["z", 1.30, 0.40],
        ]

    @combat_cache
    def jEaaa(self):
        return [
            ["j", 0.05, 0.12],

            # ["a", 0.05, 0.65],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],

            # ["a", 0.05, 0.78],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.18],

            ["a", 0.05, 0.20],

            ["w", 0.00, 1.00],
        ]

    @combat_cache
    def jEaaajaaa(self):
        return [
            ["j", 0.05, 0.12],

            # ["E", 0.05, 0.50],
            ["E", 0.05, 0.15],
            ["E", 0.05, 0.30],

            # ["a", 0.05, 0.65],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],

            # ["a", 0.05, 0.78],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.18],

            ["a", 0.05, 0.10],

            ["j", 0.05, 0.12],

            # ["a", 0.05, 0.65],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],

            # ["a", 0.05, 0.78],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.18],

            ["a", 0.05, 0.20],

            ["w", 0.00, 1.00],
        ]

    @combat_cache
    def jaaa(self):
        return [
            # jaaa
            ["j", 0.05, 0.12],

            # ["a", 0.05, 0.65],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],

            # ["a", 0.05, 0.78],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.25],
            ["a", 0.05, 0.18],

            ["a", 0.05, 0.20],

            ["w", 0.00, 1.00],
        ]

    @combat_cache
    def Q(self):
        return [
            # 声骸技能
            ["Q", 0.05, 0.00],
        ]

    @combat_cache
    def R_aero_erosion(self):
        return [
            # R 风蚀
            # ["R", 0.05, 3.67],
            ["R", 0.05, 0.20],
            ["R", 0.05, 3.42],
        ]

    @combat_cache
    def R_spectro_frazzle(self):
        return [
            # R 光噪
            # ["R", 0.05, 3.67],
            ["R", 0.05, 0.20],
            ["R", 0.05, 3.42],

            ["A", 0.05, 0.30],
            ["A", 0.05, 0.15],
        ]

    def full_combo(self):
        # 测试用，一整套连招
        return self.COMBO_SEQ

    def combo(self):
        # 祈愿能量满，福音能量空时：
        # 长按普攻 进入赦罪状态，即输出模式 加一层光噪
        # 长按E   进入告解状态，即辅助模式 加一层光噪
        # 祈愿能量上限120点，24秒涨满
        # 福音能量上限60点
        # 进入赦罪状态获得60点福音，强化重击消耗15点，伤害加深，可放4次，
        # 进入告解状态获得60点福音，强化重击消耗30点，加5层光噪，可放2次
        # 输出方式：三普攻一重击循环，把福音消耗空，等祈愿自动涨满，消耗祈愿补满福音，循环
        # 强化重击会被延奏打断，等出伤再切
        # 福音能量条黄色、角色右边漂浮库洛牌则是输出模式，福音蓝色、角色右边漂浮菱形晶石则是辅助模式
        # 专武加自身输出，延奏光噪伤害加深
        # 赞菲队使用辅助菲比

        pass
