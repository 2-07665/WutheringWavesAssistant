import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Tuple, Sequence, TypeVar, Type

import numpy as np
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class AlignEnum(Enum):
    """
    对齐方式，默认底端对齐，右对齐
    """
    BUTTON_RIGHT = "button_right"  # 底端对齐，右对齐，如角色的技能
    BUTTON_CENTER = "button_center"  # 底端对齐，水平居中，如角色的血条、能量条
    BUTTON_LEFT = "button_left"  # 底端对齐，左对齐

    TOP_RIGHT = "top_right"  # 顶端对齐，右对齐，右侧的角色头像
    TOP_CENTER = "top_center"  # 顶端对齐，水平居中，如boss血条
    TOP_LEFT = "top_left"  # 顶端对齐，左对齐，如编队左上角队伍

    CENTER = "center"  # 中心对齐，如编队
    CENTER_LEFT = "center_left"  # 垂直居中，左对齐
    CENTER_RIGHT = "center_right"  # 垂直居中，右对齐


class ResolutionEnum(Enum):
    """
    分辨率类型
    """
    STANDARD = 0  # 标准16:9
    TALL = 1  # 更高，如16:10等
    WIDE = 2  # 更宽，如21:9等


class DynamicPointTransformer:

    def __init__(self, img_or_wh: np.ndarray | tuple[int, int]):
        if isinstance(img_or_wh, tuple):
            w, h = img_or_wh
        elif isinstance(img_or_wh, np.ndarray):
            h, w = img_or_wh.shape[:2]
        else:
            raise TypeError("h_w must be either a ndarray or a tuple")
        if w == 0 or h == 0:
            raise ValueError("宽高异常，不能为0")

        self.h = h
        self.w = w
        self.ratio_16_9 = 16 / 9
        self.ratio_w_h = w / h
        self.ratio_w_1280 = w / 1280
        self.ratio_h_720 = h / 720
        self.w_diff = w - 1280 * h / 720
        self.h_diff = h - 720 * w / 1280

        if abs(self.ratio_w_h - self.ratio_16_9) <= 0.01:
            # 16:9
            resolution = ResolutionEnum.STANDARD
            # logger.debug(f"比例: 16:9")
        elif self.ratio_w_h < self.ratio_16_9:
            # 16:10等，高度更高
            resolution = ResolutionEnum.TALL
            # logger.debug(f"比例: 16:{16 * h / w:.2f}")
        else:  # self.ratio_w_h > self.ratio_16_9:
            # 21:9等，宽度更宽
            resolution = ResolutionEnum.WIDE
            # logger.debug(f"比例: 16:{16 * h / w:.2f}")
        self.resolution = resolution

    def transform(self, point: tuple[int, int], align: AlignEnum | None = None) -> tuple[int, int]:
        """ 将1280x720下的坐标转换成当前分辨率下的坐标点 """

        # 标准分辨率直接等比缩放
        if self.resolution == ResolutionEnum.STANDARD:
            return int(point[0] * self.ratio_w_1280), int(point[1] * self.ratio_w_1280)

        # 非标准分辨率，按对齐方式选择映射方式
        new_x = None
        new_y = None

        # x
        if align is None or align in [AlignEnum.BUTTON_RIGHT, AlignEnum.TOP_RIGHT, AlignEnum.CENTER_RIGHT]:  # 右对齐
            if self.resolution == ResolutionEnum.TALL:
                new_x = point[0] * self.ratio_w_1280
            elif self.resolution == ResolutionEnum.WIDE:
                new_x = self.w_diff + point[0] * self.ratio_h_720
        elif align in [AlignEnum.BUTTON_CENTER, AlignEnum.TOP_CENTER, AlignEnum.CENTER]:  # 水平居中
            if self.resolution == ResolutionEnum.TALL:
                new_x = point[0] * self.ratio_w_1280
            elif self.resolution == ResolutionEnum.WIDE:
                new_x = self.w_diff / 2 + point[0] * self.ratio_h_720
        elif align in [AlignEnum.BUTTON_LEFT, AlignEnum.TOP_LEFT, AlignEnum.CENTER_LEFT]:  # 左对齐
            if self.resolution == ResolutionEnum.TALL:
                new_x = point[0] * self.ratio_w_1280
            elif self.resolution == ResolutionEnum.WIDE:
                new_x = point[0] * self.ratio_h_720

        # y
        if align is None or align in [AlignEnum.BUTTON_RIGHT, AlignEnum.BUTTON_LEFT, AlignEnum.BUTTON_CENTER]:  # 底端对齐
            if self.resolution == ResolutionEnum.TALL:
                new_y = self.h_diff + point[1] * self.ratio_w_1280
            elif self.resolution == ResolutionEnum.WIDE:
                new_y = point[1] * self.ratio_h_720
        elif align in [AlignEnum.TOP_RIGHT, AlignEnum.TOP_LEFT, AlignEnum.TOP_CENTER]:  # 顶端对齐
            if self.resolution == ResolutionEnum.TALL:
                new_y = point[1] * self.ratio_w_1280
            elif self.resolution == ResolutionEnum.WIDE:
                new_y = point[1] * self.ratio_h_720
        elif align in [AlignEnum.CENTER, AlignEnum.CENTER_LEFT, AlignEnum.CENTER_RIGHT]:  # 垂直居中
            if self.resolution == ResolutionEnum.TALL:
                new_y = self.h_diff / 2 + point[1] * self.ratio_w_1280
            elif self.resolution == ResolutionEnum.WIDE:
                new_y = point[1] * self.ratio_h_720

        if new_x is None or new_y is None:
            logger.debug(f"new_x: {new_x}, new_y: {new_y}")
            raise ValueError("未知的枚举值")

        new_point = (int(new_x), int(new_y))
        # logger.debug(f"point: {point}, new_point: {new_point}")
        return new_point

    def untransform(self, point: tuple[int, int], align: AlignEnum | None = None) -> tuple[int, int]:
        """ 将当前分辨率下的坐标点转换成1280x720下的坐标 """

        # 标准分辨率直接等比缩放
        if self.resolution == ResolutionEnum.STANDARD:
            return int(point[0] / self.ratio_w_1280), int(point[1] / self.ratio_w_1280)

        # 非标准分辨率，按对齐方式选择映射方式
        new_x = None
        new_y = None

        # x
        if align is None or align in [AlignEnum.BUTTON_RIGHT, AlignEnum.TOP_RIGHT, AlignEnum.CENTER_RIGHT]:  # 右对齐
            if self.resolution == ResolutionEnum.TALL:
                new_x = point[0] / self.ratio_w_1280
            elif self.resolution == ResolutionEnum.WIDE:
                new_x = (point[0] - self.w_diff) / self.ratio_h_720
        elif align in [AlignEnum.BUTTON_CENTER, AlignEnum.TOP_CENTER, AlignEnum.CENTER]:  # 水平居中
            if self.resolution == ResolutionEnum.TALL:
                new_x = point[0] / self.ratio_w_1280
            elif self.resolution == ResolutionEnum.WIDE:
                new_x = (point[0] - self.w_diff / 2) * self.ratio_h_720
        elif align in [AlignEnum.BUTTON_LEFT, AlignEnum.TOP_LEFT, AlignEnum.CENTER_LEFT]:  # 左对齐
            if self.resolution == ResolutionEnum.TALL:
                new_x = point[0] / self.ratio_w_1280
            elif self.resolution == ResolutionEnum.WIDE:
                new_x = point[0] / self.ratio_h_720

        # y
        if align is None or align in [AlignEnum.BUTTON_RIGHT, AlignEnum.BUTTON_LEFT, AlignEnum.BUTTON_CENTER]:  # 底端对齐
            if self.resolution == ResolutionEnum.TALL:
                new_y = (point[1] - self.h_diff) / self.ratio_w_1280
            elif self.resolution == ResolutionEnum.WIDE:
                new_y = point[1] / self.ratio_h_720
        elif align in [AlignEnum.TOP_RIGHT, AlignEnum.TOP_LEFT, AlignEnum.TOP_CENTER]:  # 顶端对齐
            if self.resolution == ResolutionEnum.TALL:
                new_y = point[1] / self.ratio_w_1280
            elif self.resolution == ResolutionEnum.WIDE:
                new_y = point[1] / self.ratio_h_720
        elif align in [AlignEnum.CENTER, AlignEnum.CENTER_LEFT, AlignEnum.CENTER_RIGHT]:  # 垂直居中
            if self.resolution == ResolutionEnum.TALL:
                new_y = (point[1] - self.h_diff / 2) / self.ratio_w_1280
            elif self.resolution == ResolutionEnum.WIDE:
                new_y = point[1] / self.ratio_h_720

        if new_x is None or new_y is None:
            logger.debug(f"new_x: {new_x}, new_y: {new_y}")
            raise ValueError("未知的枚举值")

        new_point = (int(new_x), int(new_y))
        # logger.debug(f"point: {point}, new_point: {new_point}")
        return new_point


Pos = TypeVar('Pos', bound='Position')


class Position(BaseModel):
    """目标矩形框坐标，如文本框"""

    x1: int = Field(..., title="x1")
    y1: int = Field(..., title="y1")
    x2: int = Field(..., title="x2")
    y2: int = Field(..., title="y2")
    confidence: float = Field(0, title="识别置信度")

    def __str__(self):
        return self.model_dump_json()
        # return f"({self.x1}, {self.y1}, {self.x2}, {self.y2}, {int(self.confidence * 10000) / 10000})"

    @property
    def center(self, x_range: int = 3, y_range: int = 3) -> Tuple[int, int]:
        """中心坐标周围3格内随机"""
        middle_x = int((self.x1 + self.x2) / 2)
        middle_y = int((self.y1 + self.y2 + 2 * y_range) / 2)
        return self.point_random(middle_x, middle_y, x_range, y_range)

    @property
    def random(self) -> Tuple[int, int]:
        """当前矩形范围内随机"""
        x = int(np.random.uniform(self.x1, self.x2))
        y = int(np.random.uniform(self.y1, self.y2))
        return x, y

    @staticmethod
    def point_random(x: int, y: int, x_range: int = 3, y_range: int = 3) -> Tuple[int, int]:
        """指定的坐标周围3格内随机"""
        random_x = x + int(np.random.uniform(-x_range, x_range))
        random_y = y + int(np.random.uniform(-y_range, y_range))
        return random_x, random_y

    @classmethod
    def build(cls: Type[Pos], x1: int, y1: int, x2: int, y2: int, **kwargs) -> Pos:
        return cls(x1=x1, y1=y1, x2=x2, y2=y2, confidence=kwargs.get("confidence", 0.0), align=kwargs.get("align"))

    @classmethod
    def of(cls: Type[Pos], position: "Position") -> Pos | None:
        if position is None:
            return None
        if not isinstance(position, cls):
            raise TypeError("不是Position类或子类")
        return position

    @classmethod
    def get(cls: Type[Pos], positions: dict[str, "Position"], key: str) -> Pos:
        return cls.of(positions.get(key))


class DynamicPosition(BaseModel):
    rate: tuple[float, float, float, float] | None = Field(
        None, title="百分比矩形区域，16:9", description="左上右下两点")

    def to_position(self, height: int, width: int) -> Position:
        """百分比区域转成实际像素位置"""
        return Position.build(
            *self.to_tuple(height, width)
        )

    def to_tuple(self, height: int, width: int) -> tuple[int, int, int, int]:
        return (
            int(width * self.rate[0]),
            int(height * self.rate[1]),
            int(width * self.rate[2]),
            int(height * self.rate[3]),
        )


class TextPosition(Position, ABC):
    text: str = Field(..., title="文本")

    def __eq__(self, other):
        if isinstance(other, TextPosition):
            return (self.x1 == other.x1
                    and self.y1 == other.y1
                    and self.x2 == other.x2
                    and self.y2 == other.y2
                    # and self.confidence == other.confidence
                    and self.text == other.text)
        return False

    def __str__(self):
        return self.model_dump_json()

    @classmethod
    def build(cls: Type[Pos], x1: int, y1: int, x2: int, y2: int, **kwargs) -> Pos:
        return cls(x1=x1, y1=y1, x2=x2, y2=y2, confidence=kwargs.get("confidence", 0.0), text=kwargs.get("text"), align=kwargs.get("align"))

    @classmethod
    @abstractmethod
    def format(cls: Type[Pos], **kwargs) -> list[Pos]:
        pass


class PaddleocrPosition(TextPosition):

    @classmethod
    def format(cls: Type[Pos], output: Sequence) -> list[Pos]:
        results = output[0]
        _positions = []
        if not results:
            return _positions
        for result in results:
            text = result[1][0]
            pos = result[0]
            x1, y1, x2, y2 = pos[0][0], pos[0][1], pos[2][0], pos[2][1]
            confidence = result[1][1]
            _position = cls.build(x1=x1, y1=y1, x2=x2, y2=y2, confidence=confidence, text=text)
            _positions.append(_position)
        return _positions


class RapidocrPosition(TextPosition):

    @classmethod
    def format(cls: Type[Pos], output) -> list[Pos]:
        boxes, scores, texts = output.boxes, output.scores, output.txts
        _positions = []
        if boxes is None or len(boxes) == 0:
            return _positions
        for i in range(len(boxes)):
            box, score, text = boxes[i], scores[i], texts[i]
            _position = cls.build(x1=int(box[0][0]), y1=int(box[0][1]), x2=int(box[2][0]), y2=int(box[2][1]),
                                  confidence=score, text=text)
            _positions.append(_position)
        return _positions
