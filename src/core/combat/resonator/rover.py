import logging

from src.core.combat.combat_core import BaseResonator, CharClassEnum, ResonatorNameEnum, combat_cache
from src.core.interface import ControlService, ImgService

logger = logging.getLogger(__name__)


class BaseRover(BaseResonator):

    def __init__(self, control_service: ControlService, img_service: ImgService):
        super().__init__(control_service, img_service)

    def __str__(self):
        return self.resonator_name().name

    def resonator_name(self) -> ResonatorNameEnum:
        return ResonatorNameEnum.rover

    def char_class(self) -> list[CharClassEnum]:
        return [CharClassEnum.SubDPS]


class Rover(BaseRover):
    COMBO_SEQ = [
        ["a", 0.05, 0.30],
        ["a", 0.05, 0.30],
        ["a", 0.05, 0.30],
        ["a", 0.05, 0.30],

        ["z", 0.50, 0.50],
        ["R", 0.05, 0.50],
        ["Q", 0.05, 0.50],
    ]

    def __init__(self, control_service: ControlService, img_service: ImgService):
        super().__init__(control_service, img_service)

    @combat_cache
    def a4(self):
        return [
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],
        ]

    @combat_cache
    def a2(self):
        return [
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],
        ]

    @combat_cache
    def Eaa(self):
        return [
            ["E", 0.05, 0.50],
            ["a", 0.05, 0.30],
            ["a", 0.05, 0.30],
        ]

    @combat_cache
    def E(self):
        return [
            # 共鸣技能 E
            ["E", 0.05, 0.50],
        ]

    @combat_cache
    def z(self):
        return [
            ["z", 0.50, 0.50],
        ]

    @combat_cache
    def Q(self):
        return [
            ["Q", 0.05, 0.50],
        ]

    @combat_cache
    def R(self):
        return [
            ["R", 0.05, 0.50],
        ]

    def full_combo(self):
        # 测试用，一整套连招
        return self.COMBO_SEQ

    def combo(self):
        self.combo_action(self.a2(), True)
        self.combo_action(self.Eaa(), True)
        self.combo_action(self.z(), False)
        self.combo_action(self.a2(), True)
        self.combo_action(self.R(), False)
        self.combo_action(self.Q(), False)
