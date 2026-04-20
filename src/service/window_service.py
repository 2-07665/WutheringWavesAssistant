import logging
from threading import RLock

from src.core.contexts import Context
from src.core.exceptions import HwndError, raise_as
from src.core.geometry import Scaler
from src.core.interface import WindowService
from src.core.languages import Languages
from src.core.pages import I18nTr, I18N_TEXT, I18nText
from src.util import hwnd_util

logger = logging.getLogger(__name__)


class HwndServiceImpl(WindowService):
    """"Windows Handle to a Window"（窗口句柄）"""

    def __init__(self, context: Context):
        hwnd_util.enable_dpi_awareness()
        super().__init__()
        self._context: Context = context
        if context.spec.game_path:
            self.game_path = context.spec.game_path
        else:
            from src.util import winreg_util
            self.game_path = winreg_util.get_install_path()
        # 从gui提交的任务game_path必不为空（task monitor会为其赋值），选择强制模式用于兼容多游戏，
        # 当指定的那个游戏异常退出后，因为运行中优先原则，将会误选另一个，强制必须是这个路径的
        # 其他情况，目前没有。如无gui运行时，game_path可能没有，选择宽松模式
        self._window = hwnd_util.get_hwnd(self.game_path, bool(self.game_path))
        logger.debug("WindowService hwnd: %d", self._window)
        self._rlock: RLock = RLock()

        # runtime
        self._client_wh = None
        self._lang = None
        self._dpt = None

    @property
    def window(self):
        with self._rlock:
            if not self._window:
                raise HwndError("hwnd is None")
            return self._window

    @property
    def scaler(self) -> Scaler:
        return Scaler(self.get_client_wh())

    @property
    def tr(self) -> I18nTr:
        return I18nTr(self.get_lang())

    @raise_as(HwndError)
    def get_client_wh(self) -> tuple[int, int]:
        if self._client_wh is None:
            self._client_wh = hwnd_util.get_client_wh(self.window)
        return self._client_wh

    def refresh(self) -> bool:
        with self._rlock:
            try:
                self._window = hwnd_util.get_hwnd()
                return True
            except Exception:
                logger.exception("Get hwnd error!")
                return False

    @raise_as(HwndError)
    def get_lang(self) -> Languages:
        if self._lang is None:
            titles = I18N_TEXT.get(I18nText.GameWindowTitle)
            game_title = hwnd_util.get_hwnd_title(self.window)
            for lang, title in titles.items():
                if title == game_title:
                    self._lang = lang
                    logger.info(f"Language: {self._lang.value}")
                    break
            if self._lang is None:
                logger.error("Failed to get Language!")
        return self._lang

    @raise_as(HwndError)
    def get_ratio(self):
        """窗口大小与1280px的比例"""
        return 1280 / self.get_client_wh()[0]

    @raise_as(HwndError)
    def get_client_rect_on_screen(self) -> tuple[int, int, int, int]:
        return hwnd_util.get_client_rect_on_screen(self.window)

    @raise_as(HwndError)
    def get_window_rect(self) -> tuple[int, int, int, int]:
        return hwnd_util.get_window_rect(self.window)

    @raise_as(HwndError)
    def get_focus_rect_on_screen(self, region: tuple[float, float, float, float] | None = None) -> tuple[
        int, int, int, int]:
        return hwnd_util.get_focus_rect_on_screen(self.window, region)

    @raise_as(HwndError)
    def is_foreground_window(self) -> bool:
        return hwnd_util.is_foreground_window(self.window)

    @raise_as(HwndError)
    def close_window(self):
        hwnd_util.force_close_process(self.window)

# class NSWindowServiceImpl(WindowService):
#     pass
