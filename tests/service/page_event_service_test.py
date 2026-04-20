import logging
import os

from rapidocr import RapidOCR

from src.core.contexts import Context
from src.core.injector import Container
from src.core.interface import ControlService, OCRService, ODService, ImgService, WindowService
from src.core.pages import Page, TextMatch
from src.core.regions import RapidocrPosition
from src.service.auto_boss_service import AutoBossServiceImpl
from src.service.daily_activity_service import DailyActivityServiceImpl
from src.service.page_event_service import PageEventAbstractService
from src.util import hwnd_util, img_util, file_util, rapidocr_util, screenshot_util
from src.util.wrap_util import timeit

logger = logging.getLogger(__name__)

hwnd_util.enable_dpi_awareness()

def test_absorption_action():
    logger.debug("\n")

    os.environ["KMP_DUPLICATE_LIB_OK"] = "True"
    logger.info("任务进程开始运行")
    hwnd_util.set_window_left_top()

    context = Context()
    container = Container.build(context)
    logger.debug("Create application context")
    window_service: WindowService = container.window_service()
    img_service: ImgService = container.img_service()
    ocr_service: OCRService = container.ocr_service()
    od_service: ODService = container.od_service()
    control_service: ControlService = container.control_service()
    page_event_service: AutoBossServiceImpl = container.auto_boss_service()

    # pages = page_event_service.get_all_boss_pages()
    # conditional_actions = page_event_service.get_all_boss_conditional_actions()  # 添加boss专属条件动作
    # control_service.activate()
    #
    # page_event_service.absorption_action()


def test_page_event_static_pages():
    logger.debug("\n")
    engine: RapidOCR = rapidocr_util.create_ocr()
    # warm_img = img_util.read_img(file_util.get_assets_screenshot("Error_001.png"))
    # engine(warm_img)
    #
    pageEventAbstractService = DailyActivityServiceImpl(None, None, None, None, None, None)

    # page = pageEventAbstractService.build_UI_F2_Guidebook_Activity()
    # _test_ui_page(page, engine)
    #
    page = pageEventAbstractService.build_UI_F2_Guidebook_RecurringChallenges()
    _test_ui_page(page, engine)
    #
    # page = pageEventAbstractService.build_UI_F2_Guidebook_PathOfGrowth()
    # _test_ui_page(page, engine)
    #
    # page = pageEventAbstractService.build_UI_F2_Guidebook_EchoHunting()
    # _test_ui_page(page, engine)
    #
    # page = pageEventAbstractService.build_UI_F2_Guidebook_Milestones()
    # _test_ui_page(page, engine)
    #
    # page = pageEventAbstractService.build_UI_ESC_Terminal()
    # _test_ui_page(page, engine)
    #
    # page = pageEventAbstractService.build_UI_ESC_LeaveInstance()
    # _test_ui_page(page, engine)




def _test_ui_page(page, engine):
    for language, img_names in page.screenshot.items():
        logger.debug("language: %s, img_names: %s", language.value, img_names)
        for img_name in img_names:
            if not img_name:
                continue
            __test_ui_page(page, engine, img_name)


@timeit
def __test_ui_page(page, engine, img_name):
    logger.debug("img_name: %s", img_name)
    img = img_util.read_img(file_util.get_assets_screenshot(img_name))
    output = engine(img, use_det=True, use_rec=True, use_cls=False)
    positions = RapidocrPosition.format(output)
    is_match = page.is_match(img, img, positions)
    if not is_match:
        rapidocr_util.print_ocr_result(output)
    logger.debug("is_match: %s", is_match)
    logger.debug("matchPositions: %s", page.matchPositions)
    assert is_match


def test_page_match():
    page = Page(
        name="更新完成，请重新启动游戏",
        targetTexts=[
            TextMatch(
                name="更新完成，请重新启动游戏",
                text="更新完成，请重新启动游戏",
            ),
            TextMatch(
                name="退出",
                text="^退出$",
            ),
        ],
    )
    logger.debug("\n")
    engine: RapidOCR = rapidocr_util.create_ocr()
    hwnd = hwnd_util.get_hwnd()
    img = screenshot_util.screenshot(hwnd)
    img_util.save_img_in_temp(img)
    output = engine(img, use_det=True, use_rec=True, use_cls=False)
    positions = RapidocrPosition.format(output)
    is_match = page.is_match(img, img, positions)
    if not is_match:
        rapidocr_util.print_ocr_result(output)
    logger.debug("is_match: %s", is_match)
    logger.debug("matchPositions: %s", page.matchPositions)
    assert is_match

