import logging
import random
from dataclasses import dataclass
from enum import IntFlag
from typing import Sequence, List, Optional, Tuple

logger = logging.getLogger(__name__)


class Align(IntFlag):
    # 水平
    Left = 0x01
    Center = 0x02
    Right = 0x04

    # 垂直
    Top = 0x10
    Middle = 0x20
    Bottom = 0x40


@dataclass(frozen=True)
class Point:
    x: int
    y: int

    def as_tuple(self) -> Tuple[int, int]:
        return self.x, self.y

    def __str__(self):
        return f"Point({self.x},{self.y})"


@dataclass(frozen=True)
class AnchorPoint(Point):
    align: Align

    # ---------- 构造辅助 ----------
    @classmethod
    def of(cls, x: int, y: int, align: Align = Align.Left | Align.Top):
        return cls(x, y, align)

    @classmethod
    def from_point(cls, p: Point, align: Align):
        return cls(p.x, p.y, align)

    def as_tuple(self) -> Tuple[int, int, int]:
        return self.x, self.y, self.align.value

    def __str__(self):
        return f"AnchorPoint({self.x},{self.y},{self.align})"


@dataclass(frozen=True)
class AnchorBBox:
    p1: AnchorPoint
    p2: AnchorPoint

    @property
    def x1(self) -> int:
        return self.p1.x

    @property
    def y1(self) -> int:
        return self.p1.y

    @property
    def x2(self) -> int:
        return self.p2.x

    @property
    def y2(self) -> int:
        return self.p2.y

    def as_tuple(self) -> Tuple:
        return self.x1, self.y1, self.p1.align.value, self.x2, self.y2, self.p2.align.value

    @classmethod
    def from_list(cls, data: List[int]):
        if len(data) < 6:
            raise ValueError(f"Expected at least 6 elements, got {len(data)}")
        return cls(
            AnchorPoint(data[0], data[1], Align(data[2])),
            AnchorPoint(data[3], data[4], Align(data[5]))
        )

    def __str__(self):
        return f"AnchorBBox({self.p1},{self.p2})"


# ================= 运行态 BBox =================

@dataclass
class BBox:
    """通用矩形框（运行态：屏幕坐标 / OCR / OpenCV）"""
    x1: int
    y1: int
    x2: int
    y2: int

    # ---------- 基础 ----------
    @property
    def p1(self) -> Tuple[int, int]:
        return self.x1, self.y1

    @property
    def p2(self) -> Tuple[int, int]:
        return self.x2, self.y2

    def normalize(self) -> "BBox":
        return BBox(
            min(self.x1, self.x2),
            min(self.y1, self.y2),
            max(self.x1, self.x2),
            max(self.y1, self.y2),
        )

    # ---------- 尺寸 ----------
    def width(self) -> int:
        return self.x2 - self.x1

    def height(self) -> int:
        return self.y2 - self.y1

    def area(self) -> int:
        return self.width() * self.height()

    @property
    def center(self) -> Tuple[int, int]:
        return self.x1 + self.width() // 2, self.y1 + self.height() // 2

    # ---------- 变换 ----------
    def copy(self) -> "BBox":
        return BBox(self.x1, self.y1, self.x2, self.y2)

    def move(self, dx: int, dy: int) -> "BBox":
        bbox = self.copy()
        bbox.x1 += dx
        bbox.y1 += dy
        bbox.x2 += dx
        bbox.y2 += dy
        return bbox

    def scale(self, factor: float) -> "BBox":
        """以中心为锚点进行缩放"""
        cx, cy = self.center
        new_w = int(self.width() * factor)
        new_h = int(self.height() * factor)
        bbox = self.copy()
        bbox.x1 = cx - new_w // 2
        bbox.y1 = cy - new_h // 2
        bbox.x2 = cx + new_w // 2
        bbox.y2 = cy + new_h // 2
        return bbox

    def resize(self, factor: float) -> "BBox":
        """整体按倍率缩放"""
        bbox = self.copy()
        bbox.x1 = int(self.x1 * factor)
        bbox.y1 = int(self.y1 * factor)
        bbox.x2 = int(self.x2 * factor)
        bbox.y2 = int(self.y2 * factor)
        return bbox

    def as_tuple(self) -> Tuple[int, int, int, int]:
        return self.x1, self.y1, self.x2, self.y2

    def as_slice(self):
        """转换为 numpy 切片"""
        return slice(self.y1, self.y2), slice(self.x1, self.x2)

    # ---------------- 框判断 ----------------
    def contains_point(self, x: int, y: int) -> bool:
        return self.x1 <= x <= self.x2 and self.y1 <= y <= self.y2

    def contains_bbox(self, other: "BBox") -> bool:
        return (
                self.x1 <= other.x1 and self.y1 <= other.y1 and
                self.x2 >= other.x2 and self.y2 >= other.y2
        )

    def intersects(self, other: "BBox") -> bool:
        return not (
                self.x2 < other.x1 or
                self.x1 > other.x2 or
                self.y2 < other.y1 or
                self.y1 > other.y2
        )

    # ---------------- 随机点 ----------------
    @property
    def random(self) -> Tuple[int, int]:
        """返回框内部随机一点（不在边上），保证总能返回"""
        w, h = self.width(), self.height()
        cx, cy = self.center

        # 如果框太小，返回中心点
        if w <= 2 or h <= 2:
            return cx, cy

        x1, x2 = self.x1 + 1, self.x2 - 1
        y1, y2 = self.y1 + 1, self.y2 - 1

        # 避免 x1 > x2 或 y1 > y2
        if x1 > x2:
            x1 = x2 = cx
        if y1 > y2:
            y1 = y2 = cy

        return random.randint(x1, x2), random.randint(y1, y2)

    @property
    def near(self, factor: float = 0.3) -> Tuple[int, int]:
        """以框中心为中心，生成宽高占原框 factor 的小框，返回随机点"""
        cx, cy = self.center
        w = max(1, int(self.width() * factor))
        h = max(1, int(self.height() * factor))

        x1c = cx - w // 2
        y1c = cy - h // 2
        x2c = cx + w // 2
        y2c = cy + h // 2

        # 避免小框倒置或宽高为0
        if x1c > x2c:
            x1c = x2c = cx
        if y1c > y2c:
            y1c = y2c = cy

        return random.randint(x1c, x2c), random.randint(y1c, y2c)

    # ---------------- 合并框 ----------------
    def merge(self, other: "BBox") -> "BBox":
        """返回包含两个框的最小 BBox"""
        bbox = self.copy()
        bbox.x1 = min(self.x1, other.x1)
        bbox.y1 = min(self.y1, other.y1)
        bbox.x2 = max(self.x2, other.x2)
        bbox.y2 = max(self.y2, other.y2)
        return bbox

    @staticmethod
    def merge_overlaps(boxes: List["BBox"]) -> List["BBox"]:
        """批量合并重叠框"""
        if not boxes:
            return []
        boxes = sorted(boxes, key=lambda b: (b.y1, b.x1))
        merged = []

        while boxes:
            base = boxes.pop(0)
            i = 0
            while i < len(boxes):
                if base.intersects(boxes[i]):
                    base = base.merge(boxes.pop(i))
                    i = 0
                else:
                    i += 1
            merged.append(base)

        return merged

    def __str__(self):
        return f"BBox({self.x1},{self.y1},{self.x2},{self.y2})"


# ================= 文本框 =================

@dataclass
class TextBox(BBox):
    """带文本的矩形框"""
    text: str
    score: Optional[float] = None

    def copy(self) -> "TextBox":
        return TextBox(self.x1, self.y1, self.x2, self.y2, self.text, self.score)

    # ---------------- 置信度判断 ----------------
    def is_confident(self, threshold: float = 0.8) -> bool:
        return self.score is not None and self.score >= threshold

    def as_dict(self):
        return {
            "bbox": self.as_tuple(),
            "text": self.text,
            "score": self.score,
        }

    # ---------------- 框判断 ----------------
    def is_inside(self, other: BBox) -> bool:
        return other.contains_bbox(self)


# ================= OCR 适配 =================

class PaddleocrTextBox(TextBox):
    """PaddleOCR 输出转换为 TextBox 列表"""

    @classmethod
    def format(cls, output: Sequence) -> List["PaddleocrTextBox"]:
        results = output[0]
        textboxes = []
        if not results:
            return textboxes
        for result in results:
            coords = result[0]  # 四个点 [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
            text, score = result[1]
            x1, y1 = coords[0]
            x2, y2 = coords[2]
            textboxes.append(cls(x1, y1, x2, y2, text, score))
        return textboxes


class RapidocrTextBox(TextBox):
    """RapidOCR 输出转换为 TextBox 列表"""

    @classmethod
    def format(cls, output) -> List["RapidocrTextBox"]:
        # RapidOCROutput
        boxes, scores, texts = output.boxes, output.scores, output.txts
        textboxes = []
        if boxes is None or len(boxes) == 0:
            return textboxes
        for coords, score, text in zip(boxes, scores, texts):
            x1, y1 = int(coords[0][0]), int(coords[0][1])
            x2, y2 = int(coords[2][0]), int(coords[2][1])
            textboxes.append(cls(x1, y1, x2, y2, text, score))
        return textboxes


# ================= 缩放器 =================

class Scaler:

    def __init__(self, cur_wh: Tuple[int, int], base_wh: Tuple[int, int] = (1280, 720)):
        self.base_w, self.base_h = base_wh
        self.cur_w, self.cur_h = cur_wh

        self.scale_x = self.cur_w / self.base_w
        self.scale_y = self.cur_h / self.base_h

    # ---------- align → 比例 ----------
    def _rx(self, align: Align) -> float:
        if align & Align.Left: return 0.0
        if align & Align.Center: return 0.5
        if align & Align.Right: return 1.0
        raise ValueError(f"Invalid horizontal align: {align}")

    def _ry(self, align: Align) -> float:
        if align & Align.Top: return 0.0
        if align & Align.Middle: return 0.5
        if align & Align.Bottom: return 1.0
        raise ValueError(f"Invalid vertical align: {align}")

    def _validate_align(self, align: Align):
        hx = align & (Align.Left | Align.Center | Align.Right)
        hy = align & (Align.Top | Align.Middle | Align.Bottom)

        if hx not in (Align.Left, Align.Center, Align.Right):
            raise ValueError(f"Invalid horizontal align: {align}")

        if hy not in (Align.Top, Align.Middle, Align.Bottom):
            raise ValueError(f"Invalid vertical align: {align}")

    # ---------- AnchorPoint → Point ----------
    def as_point(self, p: AnchorPoint) -> Point:
        self._validate_align(p.align)

        rx = self._rx(p.align)
        ry = self._ry(p.align)

        base_ref_x = self.base_w * rx
        base_ref_y = self.base_h * ry

        cur_ref_x = self.cur_w * rx
        cur_ref_y = self.cur_h * ry

        dx = p.x - base_ref_x
        dy = p.y - base_ref_y

        return Point(
            int(cur_ref_x + dx * self.scale_x),
            int(cur_ref_y + dy * self.scale_y),
        )

    # ---------- AnchorBBox → BBox ----------
    def as_bbox(self, box: AnchorBBox) -> BBox:
        p1 = self.as_point(box.p1)
        p2 = self.as_point(box.p2)
        return BBox(p1.x, p1.y, p2.x, p2.y).normalize()
