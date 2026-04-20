# coding:utf-8
import logging
from typing import List

from PySide6.QtCore import Qt, Signal, QFile, QTextStream
from PySide6.QtWidgets import QApplication, QFrame, QVBoxLayout, QLabel, QWidget, QHBoxLayout, QTextBrowser, QSizePolicy
from qfluentwidgets import (FluentIcon, IconWidget, FlowLayout, isDarkTheme,
                            Theme, applyThemeColor, SmoothScrollArea, SearchLineEdit, StrongBodyLabel,
                            BodyLabel, InfoBar, InfoBarPosition, TextWrap, CardWidget)

from .gallery_interface import GalleryInterface
from ..common.translator import Translator
from ..common.config import cfg
from ..common.style_sheet import StyleSheet
from ..common.trie import Trie

logger = logging.getLogger(__name__)

class ChangelogCard(CardWidget):

    def __init__(self, content, parent=None):
        super().__init__(parent=parent)

        # self.iconWidget = IconWidget(icon, self)
        # self.titleLabel = QLabel(title, self)
        self.contentLabel = QLabel(TextWrap.wrap(content, 800, False)[0], self)

        self.hBoxLayout = QHBoxLayout(self)
        self.vBoxLayout = QVBoxLayout()

        # self.setFixedSize(1000, 90)
        self.setFixedWidth(1000)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # 宽度自适应，固定高度
        # self.iconWidget.setFixedSize(48, 48)

        self.hBoxLayout.setSpacing(28)
        self.hBoxLayout.setContentsMargins(20, 0, 20, 0)
        self.vBoxLayout.setSpacing(2)
        self.vBoxLayout.setContentsMargins(0, 15, 0, 15)
        self.vBoxLayout.setAlignment(Qt.AlignVCenter)

        self.hBoxLayout.setAlignment(Qt.AlignVCenter)
        # self.hBoxLayout.addWidget(self.iconWidget)
        self.hBoxLayout.addLayout(self.vBoxLayout)
        # self.vBoxLayout.addStretch(1)
        # self.vBoxLayout.addWidget(self.titleLabel)
        self.vBoxLayout.addWidget(self.contentLabel)
        # self.vBoxLayout.addStretch(1)

        # self.titleLabel.setObjectName('titleLabel')
        self.contentLabel.setObjectName('contentLabel')


class ChangelogCardView(QWidget):
    """ Sample card view """

    def __init__(self, title: str, parent=None):
        super().__init__(parent=parent)
        self.titleLabel = QLabel(title, self)
        self.vBoxLayout = QVBoxLayout(self)
        self.flowLayout = FlowLayout()

        self.vBoxLayout.setContentsMargins(36, 0, 36, 0)
        self.vBoxLayout.setSpacing(10)
        self.flowLayout.setContentsMargins(0, 0, 0, 0)
        self.flowLayout.setHorizontalSpacing(12)
        self.flowLayout.setVerticalSpacing(12)

        self.vBoxLayout.addWidget(self.titleLabel)
        self.vBoxLayout.addLayout(self.flowLayout)

        self.titleLabel.setObjectName('viewTitleLabel')
        StyleSheet.SAMPLE_CARD.apply(self)


    def addCard(self, content):
        """ add sample card """
        card = ChangelogCard(content, self)
        self.flowLayout.addWidget(card)


class NoticeInterface(GalleryInterface):
    """ Notice interface """

    def __init__(self, parent=None):
        # t = Translator()
        super().__init__(
            title=self.tr("Notice"),
            subtitle="https://github.com/wakening/WutheringWavesAssistant",
            parent=parent,
            subtitleSelectableByMouse=True,
        )
        self.setObjectName('noticeInterface')
        # StyleSheet.NOTICE_INTERFACE.apply(self)

        changelog_list = self.load_changelog("CHANGELOG.md")
        for changelog in changelog_list:
            self.changelogView = ChangelogCardView(changelog[0], self)
            self.changelogView.addCard(
                content="\n".join(changelog[1])
            )
            self.vBoxLayout.addWidget(self.changelogView)

    def load_changelog(self, file_path):
        changelog_list = []
        current_version = None
        current_items = None
        try:
            # file = QFile(file_path)
            # if file.open(QFile.ReadOnly | QFile.Text):
            #     stream = QTextStream(file)
            #     content = stream.readAll()
            #     file.close()
            #     return content

            file = QFile(file_path)
            if file.open(QFile.ReadOnly | QFile.Text):
                stream = QTextStream(file)
                while not stream.atEnd():  # 逐行读取，直到文件结束
                    line = stream.readLine()  # 读取一行
                    line = line.strip()  # 去除首尾空格
                    if not line:
                        continue  # 跳过空行
                    if line.startswith("v"):  # 识别版本号标题
                        current_version = line
                        current_items = []
                        changelog_list.append((current_version, current_items))
                    elif current_version:  # 版本内容
                        current_items.append(line)
                file.close()
        except Exception:
            logger.exception("Failed to load changelog")
        return changelog_list