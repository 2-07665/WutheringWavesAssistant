# coding:utf-8
from typing import List

from PySide6.QtCore import QSize, QPoint, Qt, QRect, QPropertyAnimation, QParallelAnimationGroup, QEasingCurve, QEvent, QTimer, QObject
from PySide6.QtWidgets import QLayout, QWidgetItem, QLayoutItem


class FixFlowLayout(QLayout):
    """ Flow layout """

    def __init__(self, parent=None, needAni=False, isTight=False):
        """
        Parameters
        ----------
        parent:
            parent window or layout

        needAni: bool
            whether to add moving animation

        isTight: bool
            whether to use the tight layout when widgets are hidden
        """
        super().__init__(parent)
        self._items = []    # type: List[QLayoutItem]
        self._anis = []    # type: List[QPropertyAnimation]
        self._aniGroup = QParallelAnimationGroup(self)
        self._verticalSpacing = 10
        self._horizontalSpacing = 10
        self.duration = 300
        self.ease = QEasingCurve.Linear
        self.needAni = needAni
        self.isTight = isTight
        self._deBounceTimer = QTimer(self)
        self._deBounceTimer.setSingleShot(True)
        self._deBounceTimer.timeout.connect(lambda: self._doLayout(self.geometry(), True))

        self._expandMap = {}  # anchor_index -> widget

    # =========================
    # 基础
    # =========================

    def addItem(self, item):
        self._items.append(item)

    def insertItem(self, index, item):
        index = max(0, min(index, len(self._items)))
        self._items.insert(index, item)

    def addWidget(self, w):
        super().addWidget(w)
        self._onWidgetAdded(w)

    def insertWidget(self, index, w):
        index = max(0, min(index, len(self._items)))
        self.insertItem(index, QWidgetItem(w))
        self.addChildWidget(w)
        self._onWidgetAdded(w, index)

    def _onWidgetAdded(self, w, index=-1):
        if not self.needAni:
            return

        ani = QPropertyAnimation(w, b'geometry')
        ani.setDuration(self.duration)
        ani.setEasingCurve(self.ease)
        w.setProperty('flowAni', ani)
        self._aniGroup.addAnimation(ani)

        if index == -1:
            self._anis.append(ani)
        else:
            self._anis.insert(index, ani)

    # =========================
    # Expand API
    # =========================

    def setExpandWidget(self, anchor_index: int, widget):
        if not widget:
            return

        widget.setVisible(False)
        self._expandMap[anchor_index] = widget

        if widget not in [i.widget() for i in self._items]:
            self.insertWidget(len(self._items), widget)

    def toggleExpand(self, anchor_index: int, isVisible=None):
        widget = self._expandMap.get(anchor_index)
        if not widget:
            return None

        v = widget.isVisible()
        if isVisible is None:
            widget.setVisible(not v)
            self.invalidate()
            self.activate()
        elif v != isVisible:
            widget.setVisible(isVisible)
            self.invalidate()
            self.activate()
        else:
            pass

        # widget.setVisible(not widget.isVisible())
        # self.invalidate()
        # self.activate()

        return widget.isVisible()

    # =========================
    # Layout 基础
    # =========================

    def setAnimation(self, duration, ease=QEasingCurve.Linear):
        """ set the moving animation

        Parameters
        ----------
        duration: int
            the duration of animation in milliseconds

        ease: QEasingCurve
            the easing curve of animation
        """
        if not self.needAni:
            return

        self.duration = duration
        self.ease = ease

        for ani in self._anis:
            ani.setDuration(duration)
            ani.setEasingCurve(ease)

    def count(self):
        return len(self._items)

    def itemAt(self, index: int):
        if 0 <= index < len(self._items):
            return self._items[index]

        return None

    def takeAt(self, index: int):
        """✅ 修复：必须返回 QLayoutItem"""
        if 0 <= index < len(self._items):
            item = self._items.pop(index)   # type: QLayoutItem

            w = item.widget()
            if w:
                ani = w.property('flowAni')
                if ani:
                    if ani in self._anis:
                        self._anis.remove(ani)
                    self._aniGroup.removeAnimation(ani)
                    ani.deleteLater()

            return item

        return None

    def removeWidget(self, widget):
        for i, item in enumerate(self._items):
            if item.widget() is widget:
                item = self.takeAt(i)

                if item:
                    w = item.widget()
                    if w:
                        w.hide()  # ⭐避免浮空

                return item

    def removeAllWidgets(self):
        """ remove all widgets from layout """
        while self._items:
            self.takeAt(0)

    def takeAllWidgets(self):
        """ remove all widgets from layout and delete them """
        while self._items:
            w = self.takeAt(0)
            if w:
                w.deleteLater()

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width: int):
        """ get the minimal height according to width """
        return self._doLayout(QRect(0, 0, width, 0), False)

    def setGeometry(self, rect: QRect):
        super().setGeometry(rect)

        if self.needAni:
            self._deBounceTimer.start(80)
        else:
            self._doLayout(rect, True)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()

        for item in self._items:
            size = size.expandedTo(item.minimumSize())

        m = self.contentsMargins()
        size += QSize(m.left()+m.right(), m.top()+m.bottom())

        return size

    def setVerticalSpacing(self, spacing: int):
        """ set vertical spacing between widgets """
        self._verticalSpacing = spacing

    def verticalSpacing(self):
        """ get vertical spacing between widgets """
        return self._verticalSpacing

    def setHorizontalSpacing(self, spacing: int):
        """ set horizontal spacing between widgets """
        self._horizontalSpacing = spacing

    def horizontalSpacing(self):
        """ get horizontal spacing between widgets """
        return self._horizontalSpacing

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if obj in [w.widget() for w in self._items] and event.type() == QEvent.Type.ParentChange:
            self._wParent = obj.parent()
            obj.parent().installEventFilter(self)
            self._isInstalledEventFilter = True

        if obj == self._wParent and event.type() == QEvent.Type.Show:
            self._doLayout(self.geometry(), True)
            self._isInstalledEventFilter = True

        return super().eventFilter(obj, event)

    def _doLayout(self, rect: QRect, move: bool):

        margin = self.contentsMargins()
        spaceX = self._horizontalSpacing
        spaceY = self._verticalSpacing

        # 过滤 expand
        skip_expands = set(self._expandMap.values())
        base_items = [i for i in self._items if i.widget() not in skip_expands]

        x = rect.x() + margin.left()
        y = rect.y() + margin.top()
        rowHeight = 0

        current_row = []  # [(index, item)]

        def layout_row(row_items, x, y):
            """布局一整行，并返回该行宽度"""
            if not row_items:
                return 0

            start_x = x
            cur_x = x
            max_h = 0

            widgets = []

            for idx, item in row_items:
                size = item.sizeHint()

                if move:
                    item.setGeometry(QRect(QPoint(cur_x, y), size))

                widgets.append(item.widget())

                cur_x += size.width() + spaceX
                max_h = max(max_h, size.height())

            # 真实宽度
            row_width = cur_x - spaceX - start_x
            return row_width, max_h, widgets

        i = 0
        while i < len(base_items):
            item = base_items[i]
            size = item.sizeHint()

            nextX = x + size.width() + spaceX

            if nextX - spaceX > rect.right() - margin.right() and rowHeight > 0:
                # 布局当前行
                row_width, row_h, widgets = layout_row(current_row, x_start, y)

                # 判断是否需要插入 expand（这一行）
                anchor_indexes = [idx for idx, _ in current_row if idx in self._expandMap]

                if anchor_indexes:
                    anchor_index = anchor_indexes[0]
                    expand_widget = self._expandMap[anchor_index]

                    if expand_widget.isVisible():
                        y_expand = y + row_h + spaceY

                        if move:
                            expand_widget.setFixedWidth(row_width)
                            expand_widget.setGeometry(
                                QRect(QPoint(x_start, y_expand),
                                      expand_widget.sizeHint())
                            )

                        # expand 占一整行
                        y = y_expand + expand_widget.sizeHint().height()
                    else:
                        y = y + row_h + spaceY
                else:
                    y = y + row_h + spaceY

                # 重置
                current_row = []
                x = rect.x() + margin.left()
                rowHeight = 0

                continue  # 注意：这里不 i+=1

            # 正常加入行
            if not current_row:
                x_start = x

            current_row.append((i, item))
            x += size.width() + spaceX
            rowHeight = max(rowHeight, size.height())

            i += 1

        # 最后一行
        if current_row:
            row_width, row_h, widgets = layout_row(current_row, x_start, y)

            anchor_indexes = [idx for idx, _ in current_row if idx in self._expandMap]

            if anchor_indexes:
                anchor_index = anchor_indexes[0]
                expand_widget = self._expandMap[anchor_index]

                if expand_widget.isVisible():
                    y_expand = y + row_h + spaceY

                    if move:
                        expand_widget.setFixedWidth(row_width)
                        expand_widget.setGeometry(
                            QRect(QPoint(x_start, y_expand),
                                  expand_widget.sizeHint())
                        )

                    y = y_expand + expand_widget.sizeHint().height()

        return y + rowHeight + margin.bottom() - rect.y()