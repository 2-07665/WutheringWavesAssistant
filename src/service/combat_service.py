import logging

from src.core.combat.combat_system import CombatSystem
from src.core.interface import CombatService, WindowService, ImgService, ControlService, BossInfoService

logger = logging.getLogger(__name__)


class CombatServiceImpl(CombatService):

    def __init__(self, context, window_service: WindowService, img_service: ImgService,
                 control_service: ControlService, boss_info_service: BossInfoService):
        self._context = context
        self._window_service: WindowService = window_service
        self._img_service: ImgService = img_service
        self._control_service: ControlService = control_service
        self._boss_info_service: BossInfoService = boss_info_service

        self._combat_system: CombatSystem = CombatSystem(self._control_service, self._img_service)

    def combat_system(self):
        return self._combat_system
