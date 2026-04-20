import locale
import logging
from enum import Enum

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class Languages(Enum):
    """
    BCP 47 / ISO
    """
    EN = 'en'  # English - 英语
    ZH = 'zh-CN'  # Simplified Chinese - 简体中文
    ZH_HK = 'zh-HK'  # Traditional Chinese (Hong Kong、Taiwan) - 繁体中文
    FR = 'fr'  # French - 法语
    DE = 'de'  # German - 德语
    ES = 'es'  # Spanish - 西班牙语
    JA = 'ja'  # Japanese - 日语
    KO = 'ko'  # Korean - 韩语
    RU = 'ru'  # Russian - 俄语
    PT = 'pt'  # Portuguese - 葡萄牙语
    IT = 'it'  # Italian - 意大利语
    AR = 'ar'  # Arabic - 阿拉伯语
    NL = 'nl'  # Dutch - 荷兰语
    SV = 'sv'  # Swedish - 瑞典语
    DA = 'da'  # Danish - 丹麦语
    NO = 'no'  # Norwegian - 挪威语
    FI = 'fi'  # Finnish - 芬兰语
    PL = 'pl'  # Polish - 波兰语
    TR = 'tr'  # Turkish - 土耳其语
    VI = 'vi'  # Vietnamese - 越南语
    HI = 'hi'  # Hindi - 印地语
    TH = 'th'  # Thai - 泰语
    ID = 'id'  # Indonesian - 印度尼西亚语
    HE = 'he'  # Hebrew - 希伯来语


# if __name__ == '__main__':
#     print(locale.getdefaultlocale())
#     print(locale.locale_alias)
#
#     # 测试使用
#     print(LocaleCode.ZH_CN)  # LocaleCode.ZH_CN
#     print(LocaleCode.ZH_CN.value)  # zh_CN
#     print(LocaleCode["JA_JP"])  # LocaleCode.JA_JP
#
#     # 遍历所有枚举成员
#     for locale_code in LocaleCode:
#         print(locale_code.name, "->", locale_code.value)
#
#
#     # 检查某个值是否在枚举中
#     def is_valid_locale(code):
#         return code in [item.value for item in LocaleCode]
#
#
#     print(is_valid_locale("zh_CN"))  # True
#     print(is_valid_locale("xx_XX"))  # False
