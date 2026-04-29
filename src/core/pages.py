import json
import logging
import re
import time
from abc import abstractmethod, ABC
from functools import lru_cache
from re import Pattern
from typing import Callable, Dict, List, Optional, Any

import numpy as np
from pydantic import BaseModel, Field, PrivateAttr

from src.core.boss import MoveMode, Direction
from src.core.color import ColorRule, ColorMatch, Color, RuleMode
from src.core.exceptions import StopError
from src.core.geometry import TextBox, BBox, Scaler, AnchorBBox, AnchorPoint, Align, PointKind, Point
from src.core.languages import Languages
from src.core.regions import Position, DynamicPosition, TextPosition, Pos
from src.util import img_util, file_util

logger = logging.getLogger(__name__)


class TextMatch(BaseModel):
    name: str | None = Field(None, title="文本名称，key")
    text: str | Pattern = Field(title="文本正则",
                                description="匹配用的，默认应传字符串，方便管理，除非特殊要求，才传入正则对象")
    must: bool = Field(True, title="默认True必需匹配上；False表示没有也可以，不可单独使用",
                       description="False用于将尽可能需要的文本坐标放到入参集合中，减少后续的ocr次数，不能用于定位页面")
    position: DynamicPosition | None = Field(None, title="文本范围百分比坐标",
                                             description="非空且开启就会匹配文本框是否在此区域内")
    open_position: bool = Field(True, title="是否开启文本范围限制，默认开启",
                                description="可关闭，方便用于自定义实现")

    pattern: Pattern = Field(None, description="真正最终用来匹配的")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if isinstance(self.text, str):  # 如果文本是字符串，则转换为正则表达式
            self.pattern = re.compile(self.text, re.I)  # 忽略大小写以支持英文
        else:
            self.pattern = self.text


class ImageMatch(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    # 需配置参数
    name: str | None = Field(None, title="名称，key")
    image: str | np.ndarray = Field(
        title="模板图片名，assets/template目录下", description="读取图片用的图片名称，不带路径有后缀的")
    position: DynamicPosition | None = Field(None, title="限定图片范围百分比坐标")
    confidence: float = Field(0.8, title="图片置信度", ge=0, le=1)
    open_roi_cache: bool = Field(False, title="是否开启热区缓存，只适用于绝对位置固定的图标，如全局UI图标")

    # 内部参数
    roi_cache: dict[tuple, tuple[float, tuple[int, int, int, int]]] = Field(default_factory=dict)
    img: np.ndarray = Field(None, description="真正最终用来匹配的")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if isinstance(self.image, str):  # 如果图片是路径，则读取图片
            self.img = img_util.read_img(file_util.get_assets_template(self.image))
        else:
            self.img = self.image


class ConditionalAction(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    name: str = Field(None, title="条件操作名称")
    condition: Callable[[], bool] = Field(title="条件函数", description="True则执行action函数，False则跳过")
    action: Callable[[], bool] = Field(title="操作函数列表", description="condition为True时执行")

    def __call__(self) -> bool | None:
        if self.condition is None:
            raise Exception("条件函数未设置")
        if self.condition():
            return True
        else:
            return False


class Page(BaseModel):

    @staticmethod
    def error_action(positions: dict[str, Position]) -> bool:
        raise NotImplementedError("Page callback function not implemented")

    name: str = Field(None, title="页面名称")
    action: Callable[[Dict[str, Position]], bool] = Field(default=error_action, title="页面操作函数")

    targetTexts: List[TextMatch] = Field(default_factory=list, title="目标文本")
    excludeTexts: List[TextMatch] = Field(default_factory=list, title="排除目标文本")

    targetImages: List[ImageMatch] = Field(default_factory=list, title="目标图片")
    excludeImages: List[ImageMatch] = Field(default_factory=list, title="排除目标图片")

    matchPositions: Dict[str, Position] = Field(default_factory=dict, title="匹配位置")

    screenshot: dict[Languages, list[str]] = Field(
        default_factory=dict,
        title="页面截图，默认1280x720",
        description="页面匹配了哪些页面，截图放到assets/screenshot，方便调试与排查问题，无任何运行时作用",
    )

    _target_texts_mapping: dict[str, TextMatch] = PrivateAttr()

    def __init__(self, /, **kwargs):
        super().__init__(**kwargs)
        if self.targetTexts or self.excludeTexts:
            check_must = False
            for targetText in self.targetTexts:
                check_must = check_must or targetText.must
            for excludeText in self.excludeTexts:
                check_must = check_must or excludeText.must
            if not check_must:
                raise Exception("至少得有一个是必需匹配文本，否则无法定位页面")
        self._target_texts_mapping = {}
        for i in self.targetTexts:
            self._target_texts_mapping[i.name] = i

    def __eq__(self, other):
        if isinstance(other, Page):
            return self.name == other.name
        return False

    # @timeit
    def is_match(self, src_img: np.ndarray, img: np.ndarray | None, ocr_results: list[TextPosition]) -> bool:
        """
        页面匹配
        :param src_img: 原图截图
        :param img: 缩放到标准尺寸的截图，仅在图片匹配中有用
        :param ocr_results: 识别结果
        :return: bool
        """
        # 清空匹配位置
        self.matchPositions = {}
        for text_match in self.excludeTexts:  # 遍历排除文本 如果匹配到排除文本则返回False
            if self.text_match(text_match, src_img, img, ocr_results):
                return False
        for text_match in self.targetTexts:  # 遍历目标文本 如果匹配到目标文本则记录位置 否则返回False
            position = self.text_match(text_match, src_img, img, ocr_results)
            if position:
                self.matchPositions[text_match.name] = position
            elif not text_match.must:  # 非必需文本，没匹配上也没关系
                continue
            else:
                return False
        for image_match in self.excludeImages:  # 遍历排除图片 如果匹配到排除图片则返回False
            time.sleep(0.001)  # 短暂释放CPU
            if self.image_match(image_match, src_img, img):
                return False
        for image_match in self.targetImages:  # 遍历目标图片 如果匹配到目标图片则记录位置 否则返回False
            time.sleep(0.001)  # 短暂释放CPU
            if position := self.image_match(image_match, src_img, img):
                self.matchPositions[image_match.name] = position
            else:
                return False
        logger.debug("当前页面：%s", self.name)
        return True

    def text_match(self, text_match: TextMatch, src_img: np.ndarray, img: np.ndarray,
                   ocr_results: list[TextPosition]) -> Position | None:
        """
        文本匹配
        :param text_match: 文本参数
        :param src_img: 原图图片，可能非常大，仅在最后映射回原图坐标时使用
        :param img: ocr/match用的缩放后图片，标准一般是 1280 px x Any px，16:9 就是1280x720
        :param ocr_results: ocr识别结果
        :return:
        """
        h, w = img.shape[:2]
        position = None
        logger.debug("page name: %s", self.name)
        for ocrResult in ocr_results:
            pre_match_text = ocrResult.text.strip()
            if not text_match.pattern.search(pre_match_text):  # 没找到就下一个
                logger.debug("Non-matching: %s, regex: \"%s\", ocr text: \"%s\"",
                             text_match.name, text_match.text, pre_match_text)
                continue
            if not text_match.open_position or text_match.position is None:  # 找到了，且没有限定文本区域，合格
                position = ocrResult
                logger.debug("Matching: %s, regex: \"%s\", ocr text: \"%s\"", text_match.name, text_match.text, pre_match_text)
                break
            target_position = text_match.position.to_position(h, w)  # 将百分比区域根据图片大小转成像素位置
            if self._is_subset(target_position, ocrResult):  # 限定了文本区域，看是否是该区域子集
                position = ocrResult
                logger.debug("Matching: %s, regex: %s, ocr text: %s", text_match.name, text_match.text, pre_match_text)
                break
        return self.get_real_position(src_img, img, position)

    @staticmethod
    def _is_subset(big_set: Position, small_set: Position) -> bool | None:
        """判断一个矩形位置是否为子集"""
        if big_set is None:
            return True
        if big_set.x1 > small_set.x1:
            return False
        if big_set.y1 > small_set.y1:
            return False
        if big_set.x2 < small_set.x2:
            return False
        if big_set.y2 < small_set.y2:
            return False
        return True

    def image_match(self, image_match: ImageMatch, src_img: np.ndarray, img: np.ndarray) -> Position | None:
        """
        图片模板匹配
        :param image_match: 模板参数
        :param src_img: 原图图片，可能非常大，仅在最后映射回原图坐标时使用
        :param img: ocr/match用的缩放后图片，标准一般是 1280 px x Any px，16:9 就是1280x720
        :return:
        """
        if image_match.position:  # 在限定范围内找图
            valid_pos = image_match.position.to_position(img.shape[0], img.shape[1])
            valid_img = img[valid_pos.y1:valid_pos.y2, valid_pos.x1:valid_pos.x2]
        else:
            valid_pos = None
            valid_img = img
        if image_match.open_roi_cache:  # 热区缓存，适用于固定位置，可变位置不要开启
            if cur_roi_cache := image_match.roi_cache.get(src_img.shape[:2]):
                roi: tuple[int, int, int, int] = cur_roi_cache[1]
                valid_h, valid_w = valid_img.shape[:2]
                logger.debug("get roi cache: %s", cur_roi_cache)
                roi_h, roi_w = roi[3] - roi[1], roi[2] - roi[0]
                roi_enlarge_pos = (
                    max(roi[0] - roi_w // 2, 0),
                    max(roi[1] - roi_h // 2, 0),
                    min(roi[2] + roi_w // 2, valid_w),
                    min(roi[3] + roi_h // 2, valid_h)
                )  # 选框向四周放大，不然跟模板差不多大小无法匹配
                roi_img = valid_img[roi_enlarge_pos[1]:roi_enlarge_pos[3], roi_enlarge_pos[0]:roi_enlarge_pos[2]]
                confidence, _ = img_util.match_template(roi_img, image_match.img)
                logger.debug("confidence a: %s", confidence)
                if confidence < image_match.confidence:
                    return None
                logger.debug("%s %s", self.name, confidence)
                pos_tuple = roi
            else:
                confidence, pos_tuple = result = img_util.match_template(valid_img, image_match.img)
                logger.debug("confidence b: %s", confidence)
                if confidence < image_match.confidence:
                    return None
                if confidence > 0.9:
                    image_match.roi_cache[src_img.shape[:2]] = result
        else:
            confidence, pos_tuple = img_util.match_template(valid_img, image_match.img)
            logger.debug("confidence c: %s", confidence)
            if confidence < image_match.confidence:
                return None

        if valid_pos:
            final_pos_tuple = (
                valid_pos.x1 + pos_tuple[0],
                valid_pos.y1 + pos_tuple[1],
                valid_pos.x1 + pos_tuple[2],
                valid_pos.y1 + pos_tuple[3],
            )
        else:
            final_pos_tuple = pos_tuple
        return self.get_real_position(src_img, img, Position.build(*final_pos_tuple))

    @staticmethod
    def get_real_position(src_img: np.ndarray, img: np.ndarray, position: Pos | None) -> Pos | None:
        """按缩小尺寸匹配出来的坐标，映射回原尺寸的坐标"""
        if position is None:
            return None
        ratio = src_img.shape[0] / img.shape[0]
        # _cls_obj = TextPosition if isinstance(position, TextPosition) else Position
        real_position = position.build(
            x1=int(position.x1 * ratio),
            y1=int(position.y1 * ratio),
            x2=int(position.x2 * ratio),
            y2=int(position.y2 * ratio),
            confidence=position.confidence,
            text=position.text if isinstance(position, TextPosition) else None,
        )
        logger.debug("real_position: %s", real_position)
        return real_position

    def get_text_match_by_name(self, name: str) -> TextMatch:
        return self._target_texts_mapping.get(name)

# ------- v2 -----------

def build_combined_regex(patterns: List[str], flags=re.I) -> Pattern:
    """将一组正则模式合并成一个正则对象，带命名分组"""
    grouped = [f"(?P<P{i}>{p})" for i, p in enumerate(patterns)]
    return re.compile("|".join(grouped), flags)


def match_with_index(
        text: str,
        include_patterns: List[str],
        exclude_patterns: List[str],
) -> Optional[int]:
    """匹配文本：先 exclude，再 include"""
    exclude_re = build_combined_regex(exclude_patterns) if exclude_patterns else None
    include_re = build_combined_regex(include_patterns)

    # 先匹配 exclude
    if exclude_re and exclude_re.search(text):
        return None

    # 再匹配 include
    m_inc = include_re.search(text)
    if not m_inc:
        return None

    # 返回命中 include 的下标
    for name, value in m_inc.groupdict().items():
        if value is not None:
            return int(name[1:])

    raise RuntimeError("不应该出现")  # 理论上不会触发


def flex_ws(text: str):
    """将字符串内的空白字符 替换为 任意空白正则字符串"""
    return re.sub(r"\s+", r"\\s*?", text)


class IMatch(ABC):

    @abstractmethod
    def match(self, *args, **kwargs) -> Optional[dict[str, TextBox]]:
        pass


class RegexPage(IMatch):

    class _Regex:
        def __init__(self):
            self.key = None
            self.regex_str = None
            self.pattern: Pattern = None
            self.limit: Optional[AnchorBBox] = None

    def __init__(self, page_key: str, page_dict: dict[str, Any]):
        self.page_key: str = page_key
        self.page_dict: dict[str, Any] = page_dict

        self.name = page_dict.get(I18nPage.Name)
        self.includes: list[RegexPage._Regex] = self._build_regex(I18nPage.Include)
        self.excludes: list[RegexPage._Regex] = self._build_regex(I18nPage.Exclude)
        self.assets = page_dict.get(I18nPage.Assets)

    def _build_regex(self, data_key: str, flags: int = re.I):
        data_dict: dict = self.page_dict.get(data_key)
        if not data_dict:
            return []
        rpr_list = []
        for i, (k, v) in enumerate(data_dict.items()):
            rpr = RegexPage._Regex()
            rpr.key = k
            rpr.regex_str = v
            if isinstance(v, dict):
                rpr.regex_str = v.get(I18nPage.Text)
                rpr.limit = AnchorBBox.from_list(v.get(I18nPage.Limit))
            rpr.pattern = re.compile(rpr.regex_str, flags=flags)
            rpr_list.append(rpr)
        return rpr_list

    def match(
            self,
            scaler: Scaler,
            textboxes: list[TextBox],
            **kwargs
    ) -> Optional[dict[str, TextBox]]:
        if not textboxes:
            return None

        text_excludes_result: dict[str, TextBox] = {}

        # excludes
        for rpr in self.excludes:
            # text
            for textbox in textboxes:
                # 文本匹配
                if not rpr.pattern.search(textbox.text):
                    continue

                # 位置匹配
                if not rpr.limit:
                    text_excludes_result[rpr.key] = textbox
                    break
                limit_bbox = scaler.as_bbox(rpr.limit)
                if limit_bbox.contains_bbox(textbox):
                    text_excludes_result[rpr.key] = textbox
                    break

            if len(text_excludes_result) > 0:
                logger.debug(f"text_excludes_result: {text_excludes_result}")
                return None

        text_matches_result: dict[str, TextBox] = {}

        # text_matches
        for rpr in self.includes:
            matched_textbox = None
            # text
            for textbox in textboxes:
                # 文本匹配
                if not rpr.pattern.search(textbox.text):
                    continue

                # 位置匹配
                if not rpr.limit:
                    matched_textbox = textbox
                    break
                limit_bbox = scaler.as_bbox(rpr.limit)
                if limit_bbox.contains_bbox(textbox):
                    matched_textbox = textbox
                    break

            if matched_textbox is not None:
                text_matches_result[rpr.key] = matched_textbox

        if len(text_matches_result) != len(self.includes):
            # logger.debug(f"text_matches_result: {text_matches_result}, result: False")
            return None
        logger.debug(f"text_matches_result: {text_matches_result}, result: True")

        return text_matches_result

    @staticmethod
    def error_action(positions: dict[str, Position], **kwargs) -> bool:
        raise NotImplementedError("Page callback function not implemented")


class I18nPage:
    """语义key"""
    Name = "name"
    Include = "include"
    Exclude = "exclude"
    Assets = "assets"
    # sub key
    Text = "text"
    Limit = "limit"


    class UI_ESC_Terminal:
        PAGE = "UI_ESC_Terminal"
        Terminal = "Terminal"
        Team = "Team"
        Events = "Events"
        DataBank = "DataBank"

    class Reward_LuniteSubscriptionReward:
        PAGE = "Reward_LuniteSubscriptionReward"
        Reward = "Reward"

    class Reward_ReceiveRewards:
        PAGE = "Reward_ReceiveRewards"
        ClaimRewards = "ClaimRewards"
        Confirm = "Confirm"
        Cancel = "Cancel"

    class Boss_Crownless_ResonanceCord:
        PAGE = "Boss_Crownless_ResonanceCord"
        ResonanceCord = "ResonanceCord"

    class Boss_Dreamless_Enter:
        PAGE = "Boss_Dreamless_Enter"
        Dreamless = "Dreamless"
        Heart = "Heart"
        Enter = "Enter"
        Confirm = "Confirm"
        FastTravel = "FastTravel"

    class Boss_Jue_Enter:
        PAGE = "Boss_Jue_Enter"
        Enter = "Enter"
        Confirm = "Confirm"

    class Boss_Hecate_Enter:
        PAGE = "Boss_Hecate_Enter"
        Enter = "Enter"
        Confirm = "Confirm"

    class Boss_RecommendedLevel:
        PAGE = "Boss_RecommendedLevel"
        RecommendedLevel = "RecommendedLevel"
        SoloChallenge = "SoloChallenge"
        ClaimsRemaining = "ClaimsRemaining"

    class Boss_StartChallenge:
        PAGE = "Boss_StartChallenge"
        QuickSetup = "QuickSetup"
        StartChallenge = "StartChallenge"

    class Fight_Fight:
        PAGE = "Fight_Fight"
        Fight = "Fight"
        Activity = "Activity"
        ChallengeCompleted = "ChallengeCompleted"

    class Fight_Absorption:
        PAGE = "Fight_Absorption"
        Absorb = "Absorb"
        ClaimRewards = "ClaimRewards"

    class Fight_ChallengeCompleted:
        PAGE = "Fight_ChallengeCompleted"
        ChallengeCompleted = "ChallengeCompleted"

    class Fight_ClickAlternatelyToBreakFree:
        PAGE = "Fight_ClickAlternatelyToBreakFree"
        ClickAlternatelyToBreakFree = "ClickAlternatelyToBreakFree"

    class UI_ESC_LeaveInstance:
        PAGE = "UI_ESC_LeaveInstance"
        Note = "Note"
        Confirm = "Confirm"
        Restart = "Restart"

    class Notice_LeaveInstance_NightmareHecate:
        PAGE = "Notice_LeaveInstance_NightmareHecate"
        Notice = "Notice"
        Leave = "Leave"
        Confirm = "Confirm"
        Cancel = "Cancel"

    class Notice_LoseConsciousness:
        PAGE = "Notice_LoseConsciousness"
        LoseConsciousness = "LoseConsciousness"
        Revive = "Revive"

    class Notice_SelectRevivalItem:
        PAGE = "Notice_SelectRevivalItem"
        SelectRevivalItem = "SelectRevivalItem"

    class Notice_Replenish_Waveplate:
        PAGE = "Notice_Replenish_Waveplate"
        ReplenishWaveplate = "Replenish_Waveplate"

    class Notice_BlankArea:
        PAGE = "Notice_BlankArea"
        BlankArea = "BlankArea"

    class Login_ClickLink:
        PAGE = "Login_ClickLink"
        ClickLink = "ClickLink"

    class Login_AccountLogin:
        PAGE = "Login_AccountLogin"
        Text = "Text"
        Login = "Login"
        ClickLink = "ClickLink"

    class Login_Disconnected:
        PAGE = "Login_Disconnected"
        Disconnected = "Disconnected"
        LoginTimeout = "LoginTimeout"
        Confirm = "Confirm"

    class SystemNotice_UpdateCompleteExit:
        PAGE = "SystemNotice_UpdateCompleteExit"
        UpdateComplete = "UpdateComplete"
        Exit = "Exit"

    class SystemNotice_Confirm_DriverVersion:
        PAGE = "SystemNotice_Confirm_DriverVersion"
        DriverVersion = "DriverVersion"
        Confirm = "Confirm"

    class SystemNotice_NetworkTimeout:
        PAGE = "SystemNotice_NetworkTimeout"
        SystemNotice = "SystemNotice"
        NetworkTimeout = "NetworkTimeout"
        Confirm = "Confirm"


# ------------- Global Page --------------

I18N_PAGES = {

    # ----------- UI -----------

    I18nPage.UI_ESC_Terminal.PAGE: {
        Languages.ZH: {
            I18nPage.Name: "UI-终端",
            I18nPage.Include: {
                I18nPage.UI_ESC_Terminal.Terminal: {
                    I18nPage.Text: r"^终端$",
                    I18nPage.Limit: AnchorBBox(
                        AnchorPoint(0, 0, Align.Top | Align.Left),
                        AnchorPoint(280, 90, Align.Top | Align.Left),
                    ).as_tuple(),
                },
                I18nPage.UI_ESC_Terminal.Team: r"^编队$",
                I18nPage.UI_ESC_Terminal.Events: r"^活动$",
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: ["UI_ESC_Terminal_001.png"],
        },
        Languages.EN: {
            I18nPage.Name: "UI-Terminal",
            I18nPage.Include: {
                I18nPage.UI_ESC_Terminal.Terminal: {
                    I18nPage.Text: r"^Terminal$",
                    I18nPage.Limit: AnchorBBox(
                        AnchorPoint(0, 0, Align.Top | Align.Left),
                        AnchorPoint(280, 90, Align.Top | Align.Left),
                    ).as_tuple(),
                },
                I18nPage.UI_ESC_Terminal.Team: r"^Team$",
                I18nPage.UI_ESC_Terminal.Events: r"^Events$",
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: ["UI_ESC_Terminal_001_EN.png"],
        },
    },

    # ----------- Reward -----------

    I18nPage.Reward_LuniteSubscriptionReward.PAGE: {
        Languages.ZH: {
            I18nPage.Name: "每日月卡奖励",
            I18nPage.Include: {
                I18nPage.Reward_LuniteSubscriptionReward.Reward: r"点击领取今日月相观测卡奖励",
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: ["Reward_LuniteSubscriptionReward_001.png"],
        },
        Languages.EN: {
            I18nPage.Name: "Lunite Subscription reward",
            I18nPage.Include: {
                # I18nPage.Reward_LuniteSubscriptionReward.Reward: flex_ws(r"claim today's Lunite Subscription reward"),
                I18nPage.Reward_LuniteSubscriptionReward.Reward: flex_ws(r"claim today.*Lunite Subscription reward"),
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: ["UI_ESC_Terminal_001_EN.png"],
        },
    },

    I18nPage.Reward_ReceiveRewards.PAGE: {
        Languages.ZH: {
            I18nPage.Name: "领取奖励",
            I18nPage.Include: {
                I18nPage.Reward_ReceiveRewards.ClaimRewards: r"^领取奖励$",
                I18nPage.Reward_ReceiveRewards.Confirm: r"^确认$",
                I18nPage.Reward_ReceiveRewards.Cancel: r"^取消$",
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },
    },

    # ----------- Boss -----------

    I18nPage.Boss_Crownless_ResonanceCord.PAGE: {
        Languages.ZH: {
            I18nPage.Name: "无冠者-声弦",
            I18nPage.Include: {
                I18nPage.Boss_Crownless_ResonanceCord.ResonanceCord: r"^声弦$",
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },
        Languages.EN: {
            I18nPage.Name: "Crownless-ResonanceCord",
            I18nPage.Include: {
                I18nPage.Boss_Crownless_ResonanceCord.ResonanceCord: flex_ws(r"^Resonance Cord$"),
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },
    },

    I18nPage.Boss_Dreamless_Enter.PAGE: {
        Languages.ZH: {
            I18nPage.Name: "无冠者之像·心脏",
            I18nPage.Include: {
                I18nPage.Boss_Dreamless_Enter.Dreamless: r"无冠者之像",
                I18nPage.Boss_Dreamless_Enter.Heart: r"心脏",
                I18nPage.Boss_Dreamless_Enter.Enter: r"进入",
            },
            I18nPage.Exclude: {
                I18nPage.Boss_Dreamless_Enter.Confirm: r"^确认$",
                I18nPage.Boss_Dreamless_Enter.FastTravel: r"快速旅行",
            },
            I18nPage.Assets: [],
        },
    },

    I18nPage.Boss_Jue_Enter.PAGE: {
        Languages.ZH: {
            I18nPage.Name: "角-时序之寰",
            I18nPage.Include: {
                I18nPage.Boss_Jue_Enter.Enter: r"进入时序之",
                I18nPage.Boss_Jue_Enter.Confirm: r"^确认$",
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },
    },

    I18nPage.Boss_Hecate_Enter.PAGE: {
        Languages.ZH: {
            I18nPage.Name: "声之领域|梦魇领域|最终章",
            I18nPage.Include: {
                I18nPage.Boss_Hecate_Enter.Enter: r"^(进入声之领域|进入梦.?领域|进入.*最终章.*)$",
            },
            I18nPage.Exclude: {
                I18nPage.Boss_Hecate_Enter.Confirm: r"^确认$",
            },
            I18nPage.Assets: [],
        },
    },

    I18nPage.Boss_RecommendedLevel.PAGE: {
        Languages.ZH: {
            I18nPage.Name: "推荐等级",
            I18nPage.Include: {
                I18nPage.Boss_RecommendedLevel.RecommendedLevel: r"推荐等级",
                I18nPage.Boss_RecommendedLevel.SoloChallenge: r"单人挑战",
                I18nPage.Boss_RecommendedLevel.ClaimsRemaining: r"可收取次数",
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },
    },

    I18nPage.Boss_StartChallenge.PAGE: {
        Languages.ZH: {
            I18nPage.Name: "开启挑战",
            I18nPage.Include: {
                I18nPage.Boss_StartChallenge.QuickSetup: r"^快速编队$",
                I18nPage.Boss_StartChallenge.StartChallenge: r"^开启挑战$",
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },
        Languages.EN: {
            I18nPage.Name: "StartChallenge",
            I18nPage.Include: {
                I18nPage.Boss_StartChallenge.QuickSetup: r"^QuickSetup$",
                I18nPage.Boss_StartChallenge.StartChallenge: r"^StartChallenge$",
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },
    },

    # ----------- Fight -----------

    I18nPage.Fight_Fight.PAGE: {
        Languages.ZH: {
            I18nPage.Name: "战斗画面",
            I18nPage.Include: {
                I18nPage.Fight_Fight.Fight: r"(击败|对战|泰缇斯系统|凶戾之齿|倦怠之翼|妒恨之眼|(无.?之舌)|(.?越之矛)|(.?妄之爪)|爱欲之容|盖希诺姆|(愚执之.?)|背誓之脊|遗恨之指|异海归途|荣光的灰.?)",
            },
            I18nPage.Exclude: {
                I18nPage.Fight_Fight.Activity: r"^活跃度$",
                I18nPage.Fight_Fight.ChallengeCompleted: r"^挑战成功$",
            },
            I18nPage.Assets: [],
        },
    },

    I18nPage.Fight_Absorption.PAGE: {
        Languages.ZH: {
            I18nPage.Name: "吸收",
            I18nPage.Include: {
                I18nPage.Fight_Absorption.Absorb: r"^吸收$",
            },
            I18nPage.Exclude: {
                I18nPage.Fight_Absorption.ClaimRewards: r"^领取奖励$",
            },
            I18nPage.Assets: [],
        },
    },

    I18nPage.Fight_ChallengeCompleted.PAGE: {
        Languages.ZH: {
            I18nPage.Name: "挑战成功",
            I18nPage.Include: {
                I18nPage.Fight_ChallengeCompleted.ChallengeCompleted: r"^挑战成功$",
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },
    },

    I18nPage.Fight_ClickAlternatelyToBreakFree.PAGE: {
        Languages.ZH: {
            I18nPage.Name: "交替点击进行挣脱",
            I18nPage.Include: {
                I18nPage.Fight_ClickAlternatelyToBreakFree.ClickAlternatelyToBreakFree: r"^交替点击进行挣脱$",
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },
        Languages.EN: {
            I18nPage.Name: "Click alternately to break free",
            I18nPage.Include: {
                I18nPage.Fight_ClickAlternatelyToBreakFree.ClickAlternatelyToBreakFree: flex_ws(r"^Click alternately to break free$"),
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },
    },

    # ----------- Notice -----------

    I18nPage.UI_ESC_LeaveInstance.PAGE: {
        Languages.ZH: {
            I18nPage.Name: "UI-离开副本",
            I18nPage.Include: {
                I18nPage.UI_ESC_LeaveInstance.Note: r"^提示$",
                I18nPage.UI_ESC_LeaveInstance.Confirm: r"^确认$",
                I18nPage.UI_ESC_LeaveInstance.Restart: r"^重新挑战$",
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },
        Languages.EN: {
            I18nPage.Name: "UI-LeaveInstance",
            I18nPage.Include: {
                I18nPage.UI_ESC_LeaveInstance.Note: r"^Note$",
                I18nPage.UI_ESC_LeaveInstance.Confirm: r"^Confirm$",
                I18nPage.UI_ESC_LeaveInstance.Restart: r"^Restart$",
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: ["UI_ESC_LeaveInstance_001_EN.png"],
        },
    },

    I18nPage.Notice_LeaveInstance_NightmareHecate.PAGE: {
        Languages.ZH: {
            I18nPage.Name: "Notice-离开副本-梦魇赫卡忒",
            I18nPage.Include: {
                I18nPage.Notice_LeaveInstance_NightmareHecate.Notice: r"^提示$",
                I18nPage.Notice_LeaveInstance_NightmareHecate.Leave: r"^确认离开$",
                I18nPage.Notice_LeaveInstance_NightmareHecate.Confirm: r"^确认$",
                I18nPage.Notice_LeaveInstance_NightmareHecate.Cancel: r"^取消$",
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },
        Languages.EN: {
            I18nPage.Name: "Notice-LeaveInstance-NightmareHecate",
            I18nPage.Include: {
                I18nPage.Notice_LeaveInstance_NightmareHecate.Notice: r"^Notice$",
                I18nPage.Notice_LeaveInstance_NightmareHecate.Leave: flex_ws(r"Leave this domain"),
                I18nPage.Notice_LeaveInstance_NightmareHecate.Confirm: r"^Confirm$",
                I18nPage.Notice_LeaveInstance_NightmareHecate.Cancel: r"^Cancel$",
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },
    },

    I18nPage.Notice_LoseConsciousness.PAGE: {
        Languages.ZH: {
            I18nPage.Name: "失去意识",
            I18nPage.Include: {
                I18nPage.Notice_LoseConsciousness.LoseConsciousness: r"失去意识",
                I18nPage.Notice_LoseConsciousness.Revive: r"复苏",
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },
    },

    I18nPage.Notice_SelectRevivalItem.PAGE: {
        Languages.ZH: {
            I18nPage.Name: "选择复苏物品",
            I18nPage.Include: {
                I18nPage.Notice_SelectRevivalItem.SelectRevivalItem: r"选择复苏物品",
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },
    },

    I18nPage.Notice_Replenish_Waveplate.PAGE: {
        Languages.ZH: {
            I18nPage.Name: "补充结晶波片",
            I18nPage.Include: {
                I18nPage.Notice_Replenish_Waveplate.ReplenishWaveplate: r"补充结晶波片",
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },
    },

    I18nPage.Notice_BlankArea.PAGE: {
        Languages.ZH: {
            I18nPage.Name: "空白区域",
            I18nPage.Include: {
                I18nPage.Notice_BlankArea.BlankArea: r"空白区域",
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },
    },

    # ----------- Login -----------

    I18nPage.Login_ClickLink.PAGE: {
        Languages.ZH: {
            I18nPage.Name: "点击连接",
            I18nPage.Include: {
                I18nPage.Login_ClickLink.ClickLink: r"^点击连接$",
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },
        Languages.EN: {
            I18nPage.Name: "Tap to land in Solaris-3",
            I18nPage.Include: {
                # I18nPage.Login_AccountLogin.ClickLink: flex_ws(r"Tap to land in Solaris-3"),
                I18nPage.Login_AccountLogin.ClickLink: flex_ws(r"^Tap to land in Solaris*"),
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },
    },

    I18nPage.Login_AccountLogin.PAGE: {
        Languages.ZH: {
            I18nPage.Name: "账户登录",
            I18nPage.Include: {
                I18nPage.Login_AccountLogin.Text: r"^(退出|公告|修复)$",
                I18nPage.Login_AccountLogin.Login: r"^登入$",
            },
            I18nPage.Exclude: {
                I18nPage.Login_AccountLogin.ClickLink: r"点击连接",
            },
            I18nPage.Assets: [],
        },
        Languages.EN: {
            I18nPage.Name: "AccountLogin",
            I18nPage.Include: {
                I18nPage.Login_AccountLogin.Text: r"^(Exit|Notice|Repair)$",
                I18nPage.Login_AccountLogin.Login: r"^Login$",
            },
            I18nPage.Exclude: {
                # I18nPage.Login_AccountLogin.ClickLink: flex_ws(r"Tap to land in Solaris-3"),
                I18nPage.Login_AccountLogin.ClickLink: flex_ws(r"^Tap to land in Solaris*"),
            },
            I18nPage.Assets: [],
        },
    },

    I18nPage.Login_Disconnected.PAGE: {
        Languages.ZH: {
            I18nPage.Name: "连接已断开",
            I18nPage.Include: {
                I18nPage.Login_Disconnected.Disconnected: r"连接已断开",
                I18nPage.Login_Disconnected.LoginTimeout: r"登录超时",
                I18nPage.Login_Disconnected.Confirm: r"^确认$",
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },
    },

    # ----------- System Notice -----------

    I18nPage.SystemNotice_UpdateCompleteExit.PAGE: {
        Languages.ZH: {
            I18nPage.Name: "更新完成，请重新启动游戏",
            I18nPage.Include: {
                I18nPage.SystemNotice_UpdateCompleteExit.UpdateComplete: r"更新完成.*请重新启动游戏",
                I18nPage.SystemNotice_UpdateCompleteExit.Exit: r"^退出$",
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },
    },

    I18nPage.SystemNotice_Confirm_DriverVersion.PAGE: {
        Languages.ZH: {
            I18nPage.Name: "检测到设备显卡驱动版本过旧",
            I18nPage.Include: {
                I18nPage.SystemNotice_Confirm_DriverVersion.DriverVersion: r"显卡驱动版本过旧",
                I18nPage.SystemNotice_Confirm_DriverVersion.Confirm: r"^确认$",
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },
    },

    I18nPage.SystemNotice_NetworkTimeout.PAGE: {
        Languages.ZH: {
            I18nPage.Name: "系统提示-网络请求超时",
            I18nPage.Include: {
                I18nPage.SystemNotice_NetworkTimeout.SystemNotice: r"系统提示",
                I18nPage.SystemNotice_NetworkTimeout.NetworkTimeout: r"网络请求超时",
                I18nPage.SystemNotice_NetworkTimeout.Confirm: r"^确认$",
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },
    },

}

# ------------- Echo Merge 声骸融合 --------------

class I18nPageEchoMerge(I18nPage):

    class DataBank:
        PAGE = "DataBank"
        DataBankInfo = "DataBankInfo"
        Rewards = "Rewards"

    # class DataBank_EchoGallery:
    #     PAGE = "DataBank_EchoGallery"
    #     EchoGallery = "EchoGallery"
    #
    # class DataBank_SonataGallery:
    #     PAGE = "DataBank_SonataGallery"
    #     SonataGallery = "SonataGallery"

    class DataMerge:
        PAGE = "DataMerge"
        DataMerge = "DataMerge"
        TargetedMerge = "TargetedMerge"
        StandardMerge = "StandardMerge"

    class StandardMerge_SelectAll:
        PAGE = "DataMerge_SelectAll"
        SelectAll = "SelectAll"
        DataMergeCount = "DataMergeCount"
        StandardMerge = "StandardMerge"

    class Notice_IncludesHighRarity:
        PAGE = "Notice_High_Rarity"
        Notice = "Notice"
        HighRarity = "HighRarity"
        DoNotShowAgain = "DoNotShowAgain"
        Confirm = "Confirm"

    class NewEcho:
        PAGE = "NewEcho"
        NewEcho = "NewEcho"

    # class DataBank_DataModify:
    #     PAGE = "DataBank_DataModify"
    #     DataModify = "DataModify"
    #
    # class DataBank_EchoManagement:
    #     PAGE = "DataBank_EchoManagement"
    #     EchoManagement = "EchoManagement"


I18N_PAGES_ECHO_MERGE = {
    I18nPage.UI_ESC_Terminal.PAGE: {
        Languages.ZH: {
            I18nPage.Name: "UI-终端",
            I18nPage.Include: {
                I18nPage.UI_ESC_Terminal.Terminal: {
                    I18nPage.Text: r"^终端$",
                    I18nPage.Limit: AnchorBBox(
                        AnchorPoint(0, 0, Align.Top | Align.Left),
                        AnchorPoint(280, 90, Align.Top | Align.Left),
                    ).as_tuple(),
                },
                I18nPage.UI_ESC_Terminal.Team: r"^编队$",
                I18nPage.UI_ESC_Terminal.Events: r"^活动$",
                I18nPage.UI_ESC_Terminal.DataBank: r"^数据坞$",
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: ["UI_ESC_Terminal_001.png"],
        },
        Languages.EN: {
            I18nPage.Name: "UI-Terminal",
            I18nPage.Include: {
                I18nPage.UI_ESC_Terminal.Terminal: {
                    I18nPage.Text: r"^Terminal$",
                    I18nPage.Limit: AnchorBBox(
                        AnchorPoint(0, 0, Align.Top | Align.Left),
                        AnchorPoint(280, 90, Align.Top | Align.Left),
                    ).as_tuple(),
                },
                I18nPage.UI_ESC_Terminal.Team: r"^Team$",
                I18nPage.UI_ESC_Terminal.Events: r"^Events$",
                I18nPage.UI_ESC_Terminal.DataBank: flex_ws(r"^Data Bank$"),
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: ["UI_ESC_Terminal_001_EN.png"],
        },
    },
    I18nPageEchoMerge.DataBank.PAGE: {
        Languages.ZH: {
            I18nPage.Name: "数据坞",
            I18nPage.Include: {
                I18nPageEchoMerge.DataBank.DataBankInfo: r"^数据坞信息$",
                I18nPageEchoMerge.DataBank.Rewards: r"^奖励$",
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },
        Languages.EN: {
            I18nPage.Name: "DataBank",
            I18nPage.Include: {
                I18nPageEchoMerge.DataBank.DataBankInfo: flex_ws(r"^Data Bank Info$"),
                I18nPageEchoMerge.DataBank.Rewards: r"^Rewards$",
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },

    },
    I18nPageEchoMerge.DataMerge.PAGE: {
        Languages.ZH: {
            I18nPage.Name: "数据坞-数据融合",
            I18nPage.Include: {
                I18nPageEchoMerge.DataMerge.TargetedMerge: r"定向融合$",
                I18nPageEchoMerge.DataMerge.StandardMerge: r"标准融合$",
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },
        Languages.EN: {
            I18nPage.Name: "DataBank-DataMerge",
            I18nPage.Include: {
                I18nPageEchoMerge.DataMerge.TargetedMerge: flex_ws(r"Targeted Merge$"),
                I18nPageEchoMerge.DataMerge.StandardMerge: flex_ws(r"Standard Merge$"),
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },
    },
    I18nPageEchoMerge.StandardMerge_SelectAll.PAGE: {
        Languages.ZH: {
            I18nPage.Name: "标准融合-全选",
            I18nPage.Include: {
                I18nPageEchoMerge.StandardMerge_SelectAll.SelectAll: r"^全选",
                I18nPageEchoMerge.StandardMerge_SelectAll.StandardMerge: r"^标准融合$",
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },
        Languages.EN: {
            I18nPage.Name: "StandardMerge-SelectAll",
            I18nPage.Include: {
                I18nPageEchoMerge.StandardMerge_SelectAll.SelectAll: flex_ws(r"^Select All"),
                # I18nPageEchoMerge.StandardMerge_SelectAll.DataMergeCount: flex_ws(r"Data Merge Count"),
                I18nPageEchoMerge.StandardMerge_SelectAll.StandardMerge: flex_ws(r"^Standard Merge$"),
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },
    },
    I18nPageEchoMerge.Notice_IncludesHighRarity.PAGE: {
        Languages.ZH: {
            I18nPage.Name: "提示-包含品质较高的声骸",
            I18nPage.Include: {
                I18nPageEchoMerge.Notice_IncludesHighRarity.Notice: r"^提示$",
                I18nPageEchoMerge.Notice_IncludesHighRarity.HighRarity: r"包含品质较高",
                I18nPageEchoMerge.Notice_IncludesHighRarity.DoNotShowAgain: r"本次登录不再提示",
                I18nPageEchoMerge.Notice_IncludesHighRarity.Confirm: r"^确认$",
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },
        Languages.EN: {
            I18nPage.Name: "Notice-IncludesHighRarity",
            I18nPage.Include: {
                I18nPageEchoMerge.Notice_IncludesHighRarity.Notice: flex_ws(r"^Notice$"),
                I18nPageEchoMerge.Notice_IncludesHighRarity.HighRarity: flex_ws(r"High Rarity"),
                I18nPageEchoMerge.Notice_IncludesHighRarity.DoNotShowAgain: flex_ws(r"Do not show again"),
                I18nPageEchoMerge.Notice_IncludesHighRarity.Confirm: flex_ws(r"^Confirm$"),
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },
    },
    I18nPageEchoMerge.NewEcho.PAGE: {
        Languages.ZH: {
            I18nPage.Name: "获得声骸",
            I18nPage.Include: {
                I18nPageEchoMerge.NewEcho.NewEcho: r"获得声骸",
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },
        Languages.EN: {
            I18nPage.Name: "NewEcho",
            I18nPage.Include: {
                I18nPageEchoMerge.NewEcho.NewEcho: flex_ws(r"New Echo"),
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },
    },


}

# ------------- Guidebook --------------

class I18nPageGuidebook(I18nPage):

    class Activity:
        pass

    class MaterialsSpots:
        PAGE = "MaterialsSpots"
        ForgeryChallenge = "ForgeryChallenge"
        SimulationChallenge = "SimulationChallenge"
        BossChallenge = "BossChallenge"
        TacetSuppression = "TacetSuppression"
        WeeklyChallenge = "WeeklyChallenge"
        NightmarePurification = "NightmarePurification"
        TacetDiscordNest = "TacetDiscordNest"

    class RecurringChallenges:
        pass

    class PathOfGrowth:
        pass

    class EnemyTracing:
        pass

    class Milestones:
        pass


I18N_PAGES_GUIDEBOOK = {
    I18nPageGuidebook.MaterialsSpots.PAGE: {
        Languages.ZH: {
            I18nPage.Name: "素材获取",
            I18nPage.Include: {
                # 产出武器及技能材料
                I18nPageGuidebook.MaterialsSpots.ForgeryChallenge: r"^凝素领域$",
                # 产出经验材料
                I18nPageGuidebook.MaterialsSpots.SimulationChallenge: r"^模拟领域$",
                # 产出共鸣者突破材料
                I18nPageGuidebook.MaterialsSpots.BossChallenge: r"^讨伐强敌$",
                # 产出声骸材料
                I18nPageGuidebook.MaterialsSpots.TacetSuppression: r"^无音清剿$",
                # 产出高级技能材料
                I18nPageGuidebook.MaterialsSpots.WeeklyChallenge: r"^战歌重奏$",
                # 产出梦魇声骸
                I18nPageGuidebook.MaterialsSpots.NightmarePurification: r"^梦魇祓除$",
                # 产出声骸套件
                I18nPageGuidebook.MaterialsSpots.TacetDiscordNest: r"^残像聚落$",
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },
        Languages.EN: {
            I18nPage.Name: "Materials Spots",
            I18nPage.Include: {
                I18nPageGuidebook.MaterialsSpots.ForgeryChallenge: flex_ws(r"^Forgery Challenge$"),
                I18nPageGuidebook.MaterialsSpots.SimulationChallenge: flex_ws(r"^Simulation Challenge$"),
                I18nPageGuidebook.MaterialsSpots.BossChallenge: flex_ws(r"^Boss Challenge$"),
                I18nPageGuidebook.MaterialsSpots.TacetSuppression: flex_ws(r"^Tacet Suppression$"),
                I18nPageGuidebook.MaterialsSpots.WeeklyChallenge: flex_ws(r"^Weekly Challenge$"),
                I18nPageGuidebook.MaterialsSpots.NightmarePurification: flex_ws(r"^Nightmare Purification$"),
                I18nPageGuidebook.MaterialsSpots.TacetDiscordNest: flex_ws(r"^Tacet Discord Nest$"),
            },
            I18nPage.Exclude: {},
            I18nPage.Assets: [],
        },

    },

}


class I18nText:
    # ------- game window title -------
    WutheringWaves = "WutheringWaves"

    # ------- login -------
    Login = "Login"

    # ------- map -------
    FastTravel = "FastTravel"

    # ------- combat -------
    Absorb = "Absorb"

    # ------- terminal -------
    DataBank = "DataBank"
    Guidebook = "Guidebook"

    # ------- data bank -------
    TargetedMerge = "TargetedMerge"
    StandardMerge = "StandardMerge"
    PleaseSelectAtLeast5Echoes = "PleaseSelectAtLeast5Echoes"
    DataMergeCount = "DataMergeCount"

    # ------- Guidebook -------
    Activity = "Activity"
    MaterialsSpots = "MaterialsSpots"
    RecurringChallenges = "RecurringChallenges"
    PathOfGrowth = "PathOfGrowth"
    EnemyTracing = "EnemyTracing"
    Milestones = "Milestones"

    ## ------- Guidebook MaterialsSpots -------
    ForgeryChallenge = "ForgeryChallenge"
    SimulationChallenge = "SimulationChallenge"
    BossChallenge = "BossChallenge"
    TacetSuppression = "TacetSuppression"
    WeeklyChallenge = "WeeklyChallenge"
    NightmarePurification = "NightmarePurification"
    TacetDiscordNest = "TacetDiscordNest"

    ### ------- Guidebook MaterialsSpots tacetDiscordNest -------
    # LahaiRoi = "LahaiRoi"
    StarblindCrashsiteTacetDiscordNest = "StarblindCrashsiteTacetDiscordNest"
    RebirthUplandsTacetDiscordNest = "RebirthUplandsTacetDiscordNest"
    StagnantRunTacetDiscordNest = "StagnantRunTacetDiscordNest"
    # TacetDiscordNest = "TacetDiscordNest"
    TacetDiscordDefeated = "TacetDiscordDefeated"
    Go = "Go"

    # ------- Home TacetDiscordNest -------
    ClearTheTacetDiscordNest = "ClearTheTacetDiscordNest"
    TacetDiscordNestCleared = "TacetDiscordNestCleared"


I18N_TEXT = {
    # ------- game window title -------
    I18nText.WutheringWaves: {
        Languages.ZH: "鸣潮  ",
        Languages.EN: "Wuthering Waves  ",
    },

    # ------- login -------
    I18nText.Login: {
        Languages.ZH: r"^登录$",
        Languages.EN: flex_ws(r"^Login$"),
    },

    # ------- map -------
    I18nText.FastTravel: {
        Languages.ZH: r"^快速旅行$",
        Languages.EN: flex_ws(r"^Fast Travel$"),
    },

    # ------- combat -------
    I18nText.Absorb: {
        Languages.ZH: r"^吸收$",
        Languages.EN: flex_ws(r"^Absorb$"),
    },

    # ------- terminal -------
    I18nText.DataBank: {
        Languages.ZH: r"^数据坞$",
        Languages.EN: flex_ws(r"^Data Bank$"),
    },
    I18nText.Guidebook: {
        Languages.ZH: r"^索拉指南$",
        Languages.EN: flex_ws(r"^Guidebook$"),
    },

    # ------- data bank -------
    I18nText.TargetedMerge: {
        Languages.ZH: r"^定向融合$",
        Languages.EN: flex_ws(r"^Targeted Merge$"),
    },
    I18nText.StandardMerge: {
        Languages.ZH: r"^标准融合$",
        Languages.EN: flex_ws(r"^Standard Merge$"),
    },
    I18nText.PleaseSelectAtLeast5Echoes: {
        # Languages.ZH: r"^请至少放入5个声骸",
        Languages.ZH: r"^请至少放入",
        # Languages.EN: flex_ws(r"^Please select at least 5 Echoes"),
        Languages.EN: flex_ws(r"^Please select at least"),
    },
    I18nText.DataMergeCount: {
        Languages.ZH: r"^数据融合次数",
        Languages.EN: flex_ws(r"^Data Merge Count"),
    },

    # ------- Guidebook -------
    I18nText.Activity: {
        Languages.ZH: r"^活跃度$",
        Languages.EN: flex_ws(r"^Activity$"),
    },
    I18nText.MaterialsSpots: {
        Languages.ZH: r"^素材获取$",
        Languages.EN: flex_ws(r"^Materials Spots$"),
    },
    I18nText.RecurringChallenges: {
        Languages.ZH: r"^周期挑战$",
        Languages.EN: flex_ws(r"^Recurring Challenges$"),
    },
    I18nText.PathOfGrowth: {
        Languages.ZH: r"^强者之路$",
        Languages.EN: flex_ws(r"^Path of Growth$"),
    },
    I18nText.EnemyTracing: {
        Languages.ZH: r"^敌迹探寻$",
        Languages.EN: flex_ws(r"^Enemy Tracing$"),
    },
    I18nText.Milestones: {
        Languages.ZH: r"^漂泊日志$",
        Languages.EN: flex_ws(r"^Milestones$"),
    },

    ## ------- Guidebook MaterialsSpots -------
    # 产出武器及技能材料
    I18nText.ForgeryChallenge: {
        Languages.ZH: r"^凝素领域$",
        Languages.EN: flex_ws(r"^Forgery Challenge$"),
    },
    # 产出经验材料
    I18nText.SimulationChallenge: {
        Languages.ZH: r"^模拟领域$",
        Languages.EN: flex_ws(r"^Simulation Challenge$"),
    },
    # 产出共鸣者突破材料
    I18nText.BossChallenge: {
        Languages.ZH: r"^讨伐强敌$",
        Languages.EN: flex_ws(r"^Boss Challenge$"),
    },
    # 产出声骸材料
    I18nText.TacetSuppression: {
        Languages.ZH: r"^无音清剿$",
        Languages.EN: flex_ws(r"^Tacet Suppression$"),
    },
    # 产出高级技能材料
    I18nText.WeeklyChallenge: {
        Languages.ZH: r"^战歌重奏$",
        Languages.EN: flex_ws(r"^Weekly Challenge$"),
    },
    # 产出梦魇声骸
    I18nText.NightmarePurification: {
        Languages.ZH: r"^梦魇祓除$",
        Languages.EN: flex_ws(r"^Nightmare Purification$"),
    },
    # 产出声骸套件
    I18nText.TacetDiscordNest: {
        Languages.ZH: r"^残象聚落$",
        Languages.EN: flex_ws(r"^Tacet Discord Nest$"),
    },

    ### ------- Guidebook MaterialsSpots tacetDiscordNest -------
    # I18nText.LahaiRoi: {
    #     Languages.ZH: r"^拉海洛$",
    #     Languages.EN: flex_ws(r"^Lahai-Roi$"),
    # },
    I18nText.StarblindCrashsiteTacetDiscordNest: {
        Languages.ZH: r"^盲望之塌残象聚落$",
        # Languages.EN: flex_ws(r"^Starblind Crashsite Tacet Discord Nest"),
        Languages.EN: flex_ws(r"^Starblind Crashsite"),
    },
    I18nText.RebirthUplandsTacetDiscordNest: {
        Languages.ZH: r"^复生丘原残象聚落$",
        # Languages.EN: flex_ws(r"^Rebirth Uplands Tacet Discord Nest"),
        Languages.EN: flex_ws(r"^Rebirth Uplands"),
    },
    I18nText.StagnantRunTacetDiscordNest: {
        Languages.ZH: r"^陷足流川残象聚落$",
        # Languages.EN: flex_ws(r"^Stagnant RunTacet Discord Nest"),
        Languages.EN: flex_ws(r"^Stagnant Run"),
    },
    I18nText.TacetDiscordDefeated: {
        # 已击败残象:0/48
        Languages.ZH: r"^已击败残象.*\d.*",
        # TDs defeated: 0/48
        Languages.EN: flex_ws(r"^TDs defeated.*\d.*"),
    },
    I18nText.Go: {
        Languages.ZH: r"^前往$",
        Languages.EN: flex_ws(r"^Go$"),
    },

    # ------- Home TacetDiscordNest -------
    I18nText.ClearTheTacetDiscordNest: {
        Languages.ZH: r"^清理聚落中的残象$",
        Languages.EN: flex_ws(r"^Clear the Tacet Discord Nest$"),
    },
    I18nText.TacetDiscordNestCleared: {
        Languages.ZH: r"^残象聚落已清理$",
        Languages.EN: flex_ws(r"^Tacet Discord Nest Cleared$"),
    },



}


class I18nTr:

    def __init__(self, lang: Languages):
        self._lang = lang

    def __call__(self, text_key: str):
        return self.t(text_key)

    def t(self, text_key: str):
        return I18N_TEXT.get(text_key).get(self._lang)


class I18nPageX:

    def __init__(self, data: dict | str):
        self.data: dict = json.loads(data) if isinstance(data, str) else data
        self.i18n_regex_pages: dict[Languages, dict[str, RegexPage]] = {}
        for page_key, k_lang_v_page in self.data.items():
            for k_lang, v_page in k_lang_v_page.items():
                self.i18n_regex_pages.setdefault(k_lang, {})[page_key] = RegexPage(page_key, v_page)


@lru_cache(maxsize=2000)
def _cached_compile_regex(regex_str: str, flags=re.I) -> Pattern:
    return re.compile(regex_str, flags)


class OcrResult:

    def __init__(self, results: list[TextBox]):
        self.results: list[TextBox] = results

    def has_results(self) -> bool:
        return self.results is not None and len(self.results) > 0

    def search(
            self, regex_str: str | list[str], roi: Optional[BBox] = None, flags=re.I
    ) -> Optional[list[TextBox]]:
        """ 在结果中搜索符合正则的文本 """
        return self.__search(regex_str, roi, flags, False)

    def search_with_index(
            self, regex_str: str | list[str], roi: Optional[BBox] = None, flags=re.I
    ) -> Optional[list[tuple[int, TextBox]]]:
        """ 在结果中搜索符合正则的文本 带索引 """
        return self.__search(regex_str, roi, flags, True)

    def __search(
            self,
            regex_str: str | list[str],
            roi: Optional[BBox] = None,
            flags=re.I,
            with_index: bool = False,
    ):
        """
        搜索文本
        :param regex_str: 支持正则
        :param roi: 支持框定文本位置范围
        :param flags: 默认忽略大小写
        :param with_index: 是否带下标索引，下标为regex_str的下标
        :return:
        """
        if not regex_str:
            raise ValueError()
        if not self.has_results():
            return None
        found_boxes = []
        regex_str = [regex_str] if isinstance(regex_str, str) else regex_str
        patterns = [_cached_compile_regex(i, flags) for i in regex_str]
        for text_box in self.results:
            for index, pattern in enumerate(patterns):
                match = pattern.search(text_box.text)
                if not match:
                    continue
                if roi and not roi.contains_bbox(text_box):
                    continue
                if with_index:
                    found_boxes.append((index, text_box))
                else:
                    found_boxes.append(text_box)
        return found_boxes

    def search_group(
            self, regex_str: str | list[str], roi: Optional[TextBox] = None, flags=re.I
    ) -> Optional[list[TextBox]]:
        """ 合并搜索 """
        if not regex_str:
            raise ValueError()
        if not self.has_results():
            return None
        match_list = []
        if isinstance(regex_str, str):
            pattern = _cached_compile_regex(regex_str, flags)
        else:
            # 输入正则内有括号下标会加一错位
            pattern = build_combined_regex(regex_str, flags)
        for text_box in self.results:
            m_inc = pattern.search(text_box.text)
            if not m_inc:
                continue
            if not roi or roi.contains_bbox(text_box):
                match_list.append(text_box)
        return match_list


class Wait:

    def __init__(self, timeout: float, interval: float):
        self.timeout = timeout  # 单位都是秒
        self.interval = interval

    def until(self, fn, *, predicate=bool):
        deadline = time.monotonic() + self.timeout

        while time.monotonic() < deadline:
            res = fn()
            if predicate(res):
                return res
            time.sleep(self.interval)

        return None


class OcrQuery:
    """ 整合一些常用的Ocr操作，减少重复代码 """

    def __init__(self, ctx):
        self.ctx = ctx
        self.img = None
        self.results: OcrResult = None
        # 保证每张图只查一次，及时抛出异常提醒
        self._is_query = False

    def grab(self, img: Optional[np.ndarray] = None) -> "OcrQuery":
        if img is None:
            self.img = self.ctx.img_service.screenshot()
        else:
            self.img = img
        self._is_query = False
        return self

    def query(self) -> "OcrQuery":
        if self._is_query:
            raise Exception("OcrQuery is already query")
        self.results = self.ctx.ocr_service.query(self.img)
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"ocr result: {self.results.results}")
        self._is_query = True
        return self

    def has_results(self) -> bool:
        return bool(self.results) and self.results.has_results()

    def search(self, regex_str: str | list[str], roi: Optional[BBox] = None, flags=re.I) -> Optional[list[TextBox]]:
        if not self.results:
            return None
        return self.results.search(regex_str, roi, flags)

    def search_with_index(self, regex_str: str | list[str], roi: Optional[BBox] = None, flags=re.I) -> Optional[list[tuple[int, TextBox]]]:
        if not self.results:
            return None
        return self.results.search_with_index(regex_str, roi, flags)

    def poll(self, func, timeout: float = 3.0, interval: float = 0.1):
        start = time.monotonic()
        end = start + timeout
        while True:
            result = func()
            if result:
                return result
            if time.monotonic() >= end:
                return None
            time.sleep(interval)

    def wait(self, timeout: float = 3.0, interval: float = 0.1):
        return Wait(timeout, interval)


class UIOp:
    """
    UI Operation
    整合一些常用的ui操作，减少重复代码
    """

    def __init__(self, ctx, page_service=None):
        self.ctx = ctx
        self.oq = OcrQuery(self.ctx)
        # 绑定页面，在指定页面内搜索，默认为全局公共页面
        self.page_service = page_service if page_service else self.ctx.page_service

        # runtime
        self.__color_match = None

    def grap(self):
        return self.ctx.img_service.screenshot()

    def snapshot(self, img: Optional[np.ndarray] = None):
        self.oq = OcrQuery(self.ctx).grab(img).query()
        return self

    def is_match(self, page: str):
        return self.page_service.is_match(self.oq.results, page)

    def search(self, regex_str: str | list[str], roi: Optional[BBox] = None, flags=re.I) -> Optional[list[TextBox]]:
        return self.oq.search(regex_str, roi, flags)

    def search_by_key(
            self, i18n_text: str | list[str], roi: Optional[BBox] = None, flags=re.I) -> Optional[list[TextBox]]:
        i18n_text = i18n_text if isinstance(i18n_text, list) else [i18n_text]
        return self.oq.search([self.ctx.tr(i) for i in i18n_text], roi, flags)

    def search_with_index(
            self, regex_str: str | list[str], roi: Optional[BBox] = None, flags=re.I
    ) -> Optional[list[tuple[int, TextBox]]]:
        return self.oq.search_with_index(regex_str, roi, flags)

    def wait(self, timeout: float = 3.0, interval: float = 0.1):
        return self.oq.wait(timeout, interval)

    def __click(self, x: int, y: int, times: int = 1, interval: float = 0.0):
        if times < 1 or interval < 0:
            raise ValueError(f"Invalid value: {times} / {interval}")
        for i in range(times):
            self.ctx.control_service.click(x, y)
            if times > 1:
                self.sleep(interval)
        return self

    def click_point(self, point: Point, times: int = 1, interval: float = 0.0):
        if isinstance(point, AnchorPoint):
            point = self.ctx.scaler.as_point(point)
        self.__click(point.x, point.y, times, interval)
        return self

    def click_bbox(self, bbox: BBox, pk: PointKind = PointKind.CENTER, times: int = 1, interval: float = 0.0):
        if isinstance(bbox, AnchorBBox):
            bbox = self.ctx.scaler.as_bbox(bbox)
        if pk == PointKind.CENTER:
            point = bbox.center
        elif pk == PointKind.NEAR:
            point = bbox.near
        elif pk == PointKind.RANDOM:
            point = bbox.random
        else:
            raise ValueError("Unsupported PointKind")
        self.__click(point[0], point[1], times, interval)
        return self

    def click_key(self, match, key, pk: PointKind = PointKind.CENTER):
        bbox = match.get(key)
        self.click_bbox(bbox, pk)
        return self

    def click_text(
        self,
        regex_str: str | list[str],
        roi: Optional[BBox] = None,
        index: int = 0,
        pk: PointKind = PointKind.CENTER,
        times: int = 1,
        interval: float = 0.0,
    ) -> bool:
        res = self.search(regex_str, roi)
        if not res or len(res) <= index:
            return False
        self.click_bbox(res[index], pk, times, interval)
        return True

    def sleep(self, t):
        if not self.ctx.runtime.stop_event.is_set():
            raise StopError()
        time.sleep(t)
        if not self.ctx.runtime.stop_event.is_set():
            raise StopError()
        return self

    def esc(self):
        self.ctx.control_service.esc()
        return self

    def activate(self):
        self.ctx.control_service.activate()
        return self

    def trs(self, texts: list[str]) -> list[str]:
        """批量翻译"""
        return [self.ctx.tr(text) for text in texts]

    def __init_color_match(self):
        points = [
            # 任务
            AnchorPoint(14, 153, Align.Top | Align.Left), AnchorPoint(26, 152, Align.Top | Align.Left),
            # 背包
            AnchorPoint(214, 44, Align.Top | Align.Left), AnchorPoint(222, 44, Align.Top | Align.Left),
            # 飞讯
            AnchorPoint(274, 31, Align.Top | Align.Left), AnchorPoint(280, 38, Align.Top | Align.Left),
            # # 先约电台
            # AnchorPoint(1114, 24, Align.Top | Align.Right),
            # 共鸣者
            AnchorPoint(1156, 28, Align.Top | Align.Right), AnchorPoint(1160, 30, Align.Top | Align.Right),
            # 终端
            AnchorPoint(1221, 34, Align.Top | Align.Right), AnchorPoint(1222, 35, Align.Top | Align.Right),
        ]
        rule = ColorRule().points(points).colors(Color.bgr(255, 255, 255), 10, RuleMode.ALL)
        self.__color_match = ColorMatch(self.ctx.scaler).rules(rule)

    def wait_back_home(self, timeout: int = 60, interval: float = 1.0):
        """ 循环等待回到主界面 """
        if not self.__color_match:
            self.__init_color_match()

        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            self.activate().sleep(0.1)
            img = self.grap()
            if self.__color_match.match(img):
                return self
            self.sleep(interval)

        # 卡在加载，强制关闭
        self.ctx.control_service.close_window()
        raise Exception("等待回到主界面超时")

    def execute_route(self, route_steps):
        """执行路线步骤"""
        for step in route_steps:
            if step.mode == MoveMode.WALK:
                self._execute_walk_step(step)
            elif step.mode == MoveMode.RUN:
                self._execute_run_step(step)

    def _execute_walk_step(self, step):
        """执行行走步骤"""
        if step.steps and step.steps > 0:
            self.ctx.control_service.forward_walk(
                step.steps, Direction.get_key(step.direction)
            )
        elif step.duration and step.duration > 0:
            # 行走模式按时间移动（待实现）
            pass

    def _execute_run_step(self, step):
        """执行跑步步骤"""
        if step.steps and step.steps > 0:
            # 跑步模式按步数移动（待实现）
            pass
        elif step.duration and step.duration > 0:
            self.ctx.control_service.forward_run(
                step.duration, Direction.get_key(step.direction)
            )



if __name__ == '__main__':
    # patterns = [
    #     r"cat",
    #     r"dog",
    #     r"\d+"
    # ]
    #
    # regex = build_combined_regex(patterns)
    #
    # print(match_with_index(regex, "hello dog world"))
    # # (True, 1)
    #
    # print(match_with_index(regex, "abc 123"))
    # # (True, 2)
    #
    # print(match_with_index(regex, "nothing"))
    # # (False, None)
    print(I18nPageEchoMerge.StandardMerge_SelectAll.__name__)