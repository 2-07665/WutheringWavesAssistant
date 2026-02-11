# 连招定制开发指南

本文档指导开发者如何为新角色开发定制连招，包括技能检测、连招设计和测试验证。

---

## 📚 目录

1. [开发前准备](#开发前准备)
2. [Base 类开发](#base-类开发)
3. [连招实现类开发](#连招实现类开发)
4. [注册与测试](#注册与测试)
5. [最佳实践](#最佳实践)
6. [常见问题](#常见问题)

---

## 开发前准备

### 所需工具

1. **截图工具** - 用于获取游戏画面
2. **取色器** - 推荐使用 PowerToys 的取色器或类似工具
3. **Python 开发环境** - Python 3.10-3.12
4. **游戏环境** - 训练场或实战环境

### 所需知识

1. 熟悉角色的技能机制和连招循环
2. 了解像素坐标系统（1280×720 为基准分辨率）
3. 基础 Python 编程能力

### 文件结构

```
src/core/combat/resonator/
├── your_character.py  # 新角色文件
└── ...

src/core/combat/
├── combat_core.py     # 基类定义
└── combat_system.py   # 战斗系统，需要注册
```

---

## Base 类开发

### 第一步：创建角色文件

在 `src/core/combat/resonator/` 目录下创建新文件 `your_character.py`。

### 第二步：定义 Base 类框架

```python
import logging
import numpy as np

from src.core.combat.combat_core import ColorChecker, BaseResonator, CharClassEnum, LogicEnum, ResonatorNameEnum
from src.core.interface import ControlService, ImgService

logger = logging.getLogger(__name__)


class BaseYourCharacter(BaseResonator):

    def __init__(self, control_service: ControlService, img_service: ImgService):
        super().__init__(control_service, img_service)

        # 在这里定义所有技能检测器

    def __str__(self):
        return self.resonator_name().name

    def resonator_name(self) -> ResonatorNameEnum:
        return ResonatorNameEnum.your_character  # 需要先在 combat_core.py 中添加枚举

    def char_class(self) -> list[CharClassEnum]:
        # 返回角色定位：MainDPS / SubDPS / Support / Healer
        return [CharClassEnum.MainDPS]

    # 实现所有必需的检测方法
```

### 第三步：获取技能图标坐标

**操作步骤**：

1. 在训练场进入战斗状态
2. 截取 1280×720 分辨率的游戏画面
3. 使用取色器获取技能图标**亮起时**的白色像素坐标
4. 记录坐标和颜色值

**关键点位**（基于 1280×720）：

```python
# 示例坐标（需要根据实际角色调整）

# 协奏能量（血条旁的彩色圈）
# - 红圈: ColorChecker.concerto_fusion()
# - 黄圈: ColorChecker.concerto_spectro()
# - 蓝圈: ColorChecker.concerto_glacio()
# - 绿圈: ColorChecker.concerto_aero()
# - 紫圈: ColorChecker.concerto_havoc()
self._concerto_energy_checker = ColorChecker.concerto_fusion()

# 共鸣技能 E（右下角 E 技能图标）
self._resonance_skill_point = [(1074, 635), (1091, 634), (1082, 658)]
self._resonance_skill_color = [(255, 255, 255)]  # 白色 BGR
self._resonance_skill_checker = ColorChecker(
    self._resonance_skill_point,
    self._resonance_skill_color
)

# 声骸技能 Q（右下角 Q 技能图标）
self._echo_skill_point = [(1146, 632), (1141, 652), (1160, 656)]
self._echo_skill_color = [(255, 255, 255)]
self._echo_skill_checker = ColorChecker(
    self._echo_skill_point,
    self._echo_skill_color
)

# 共鸣解放 R（右下角 R 技能图标）
self._resonance_liberation_point = [(1202, 657), (1219, 656)]
self._resonance_liberation_color = [(255, 255, 255)]
self._resonance_liberation_checker = ColorChecker(
    self._resonance_liberation_point,
    self._resonance_liberation_color
)
```

### 第四步：特殊状态检测

如果角色有特殊机制（如能量条、变身状态、buff 状态），需要额外定义检测器：

```python
# 示例：能量格数检测
self._energy1_point = [(547, 668), (548, 668), (552, 668)]
self._energy1_color = [(107, 97, 250)]  # BGR
self._energy1_checker = ColorChecker(
    self._energy1_point,
    self._energy1_color
)

# 能量检测方法
def energy_count(self, img: np.ndarray) -> int:
    energy_count = 0
    if self._energy1_checker.check(img):
        energy_count = 1
    if self._energy2_checker.check(img):
        energy_count = 2
    # ... 更多能量格
    logger.debug(f"{self.resonator_name().value}-能量: {energy_count}格")
    return energy_count
```

### 第五步：实现检测方法

为每个技能实现检测方法：

```python
def is_resonance_skill_ready(self, img: np.ndarray) -> bool:
    is_ready = self._resonance_skill_checker.check(img)
    logger.debug(f"{self.resonator_name().value}-共鸣技能: {is_ready}")
    return is_ready

def is_echo_skill_ready(self, img: np.ndarray) -> bool:
    is_ready = self._echo_skill_checker.check(img)
    logger.debug(f"{self.resonator_name().value}-声骸技能: {is_ready}")
    return is_ready

def is_resonance_liberation_ready(self, img: np.ndarray) -> bool:
    is_ready = self._resonance_liberation_checker.check(img)
    logger.debug(f"{self.resonator_name().value}-共鸣解放: {is_ready}")
    return is_ready

def is_concerto_energy_ready(self, img: np.ndarray) -> bool:
    is_ready = self._concerto_energy_checker.check(img)
    logger.debug(f"{self.resonator_name().value}-协奏: {is_ready}")
    return is_ready
```

**注意事项**：

1. **LogicEnum.OR vs AND**：
   - `OR`（默认）：任一点匹配即返回 True，适用于简单的亮/灰状态
   - `AND`：所有点都匹配才返回 True，适用于有多种状态变化的技能

2. **颜色容差**：
   - 默认容差为 30
   - 对于颜色变化大的技能，可调整 `tolerance` 参数

---

## 连招实现类开发

### 第一步：定义实现类框架

```python
class YourCharacter(BaseYourCharacter):
    # COMBO_SEQ 为训练场单人静态完整连段，后续开发以此为准从中拆分截取

    COMBO_SEQ = [
        # 完整连招序列（参考用）
        ["a", 0.05, 0.30],
        ["a", 0.05, 0.30],
        # ...
    ]

    def __init__(self, control_service: ControlService, img_service: ImgService):
        super().__init__(control_service, img_service)

    # 定义连招片段方法

    def combo(self):
        # 连招主逻辑
        pass
```

### 第二步：定义动作序列格式

每个动作为三元组 `[key, press_time, wait_time]`：

```python
# 格式: [按键, 按下时长(秒), 等待时长(秒)]

["a", 0.05, 0.30]  # 普攻：按下0.05秒，等待0.30秒
["E", 0.05, 1.25]  # E技能：按下0.05秒，等待1.25秒
["z", 3.50, 0.41]  # 重击：长按3.50秒，等待0.41秒
["R", 0.05, 2.63]  # 大招：按下0.05秒，等待2.63秒
["Q", 0.05, 0.50]  # 声骸：按下0.05秒，等待0.50秒
["j", 0.05, 0.30]  # 跳跃：按下0.05秒，等待0.30秒
["d", 0.05, 0.30]  # 闪避：按下0.05秒，等待0.30秒
["w", 0.00, 1.00]  # 前进（通常用于间隔）：等待1.00秒
```

**按键说明**：

| 按键 | 游戏操作 | 说明 |
|------|----------|------|
| `a` | 鼠标左键 | 普攻（按下时长 ≤ 0.2秒） |
| `z` | 鼠标左键 | 重击（按下时长 ≥ 0.3秒） |
| `E` | E键 | 共鸣技能 |
| `R` | R键 | 共鸣解放 |
| `Q` | Q键 | 声骸技能 |
| `j` | 空格 | 跳跃 |
| `d` | Shift/鼠标右键 | 闪避 |
| `w` | W键 | 前进（通常用于间隔，press_time 填 0.00） |
| `G` | G键 | 瞄准（枪系角色） |

### 第三步：设计连招片段

将完整连招拆分为可复用的片段：

```python
def a4(self):
    """4段普攻"""
    logger.debug("a4")
    return [
        ["a", 0.05, 0.30],
        ["a", 0.05, 0.30],
        ["a", 0.05, 0.30],
        ["a", 0.05, 0.30],
    ]

def E(self):
    """E技能"""
    logger.debug("E")
    return [
        ["E", 0.05, 1.25],
    ]

def R(self):
    """共鸣解放"""
    logger.debug("R")
    return [
        ["R", 0.05, 2.50],
    ]

def Q(self):
    """声骸技能"""
    logger.debug("Q")
    return [
        ["Q", 0.05, 0.50],
    ]

def a4E(self):
    """4段普攻接E技能"""
    logger.debug("a4E")
    return [
        ["a", 0.05, 0.30],
        ["a", 0.05, 0.30],
        ["a", 0.05, 0.30],
        ["a", 0.05, 0.30],
        ["E", 0.05, 1.25],
    ]
```

**连招拆分策略**：

1. **基础片段**：单个技能或简单组合（如 `a4()`, `E()`, `R()`）
2. **组合片段**：常用连招组合（如 `a4E()`, `Eza()`）
3. **长等待拆分**：将长时间等待拆成多段短等待，提高容错性

```python
# 不推荐：长时间发呆
["a", 0.05, 0.90]

# 推荐：拆分成多段
["a", 0.05, 0.30],
["a", 0.05, 0.30],
["a", 0.05, 0.30],
```

### 第四步：实现 combo() 主逻辑

`combo()` 是连招的核心方法，负责：
1. 截图检测当前状态
2. 根据状态决策连招路线
3. 调用 `combo_action()` 执行动作序列

**标准模板**：

```python
def combo(self):
    """连招主逻辑"""

    # 1. 截图检测所有状态
    img = self.img_service.screenshot()

    is_resonance_skill_ready = self.is_resonance_skill_ready(img)
    is_echo_skill_ready = self.is_echo_skill_ready(img)
    is_resonance_liberation_ready = self.is_resonance_liberation_ready(img)
    is_concerto_energy_ready = self.is_concerto_energy_ready(img)
    energy_count = self.energy_count(img)  # 需要在 Base 类中覆写此方法
    boss_hp = self.boss_hp(img)  # Boss 血量检测

    # 2. 释放声骸技能（通常优先级较低，提前释放用于合轴）
    self.combo_action(self.Q(), False)

    # 3. 连招决策树（优先级从高到低）

    # 优先级1: 共鸣解放（大招）
    if is_resonance_liberation_ready:
        self.combo_action(self.R(), True)
        return

    # 优先级2: 特殊状态处理
    if energy_count >= 4 and is_resonance_skill_ready:
        self.combo_action(self.a4E(), False)
        return

    # 优先级3: E技能循环
    if is_resonance_skill_ready:
        self.combo_action(self.a4E(), False)
        return

    # 优先级4: 兜底普攻
    self.combo_action(self.a4(), False)
```

**关键参数说明**：

- `combo_action(sequence, end_wait, ignore_event=False)`
  - `sequence`: 动作序列
  - `end_wait`: 是否等待最后一个动作的后摇
    - `True`: 等待完整后摇（放完技能才切人）
    - `False`: 不等待（一放就切，用于合轴）
  - `ignore_event`: 是否忽略暂停事件（通常不用）

**决策优先级建议**：

1. **共鸣解放 (R)** - 最高优先，有大开大
2. **特殊状态** - 角色特有机制（如椿的盛绽、安可的暴走）
3. **共鸣技能 (E)** - 核心技能循环
4. **声骸技能 (Q)** - 通常最后释放用于合轴
5. **普攻连段** - 兜底选项

### 第五步：高级技巧

#### 1. Boss 血量判断

避免 Boss 击败后空输出：

```python
boss_hp = self.boss_hp(img)
if boss_hp <= 0.01:
    # Boss 即将击败，跳过长连招
    self.combo_action(self.a4(), False)
    return
```

#### 2. 异常处理

某些角色需要处理特殊状态（如被打断、飞出场外）：

```python
def combo(self):
    try:
        # 正常连招逻辑
        img = self.img_service.screenshot()
        # ...
    except StopError as e:
        # 被打断时的清理操作
        self.control_service.jump()  # 例如：打断变身
        raise e
```

#### 3. 随机选择

为某些技能添加随机性（如声骸技能）：

```python
def Q(self):
    """声骸技能 - 随机选择梦魇摩托或普通摩托"""
    if self.random_float() < 0.33:
        # 33% 概率使用梦魇摩托（长按）
        return [
            ["Q", 4.00, 0.50],
        ]
    else:
        # 67% 概率使用普通摩托（短按）
        return [
            ["Q", 0.05, 0.50],
        ]
```

#### 4. 入场检测

为变奏（延奏）入场提供特殊处理：

```python
# 在 Base 类中定义入场状态检测器
self._resonance_skill_incoming_color = [(173, 238, 249)]  # 黄色入场状态
self._resonance_skill_incoming_checker = ColorChecker(
    self._resonance_skill_point,
    self._resonance_skill_incoming_color,
    tolerance=50
)

# 在 combo() 中优先检测入场状态
def combo(self):
    img = self.img_service.screenshot()

    is_incoming = self.is_resonance_skill_incoming_ready(img)
    if is_incoming:
        # 入场特殊连招
        self.combo_action(self.incoming_combo(), False)
        return

    # 正常连招逻辑...
```

---

## 注册与测试

### 第一步：添加角色枚举

在 `src/core/combat/combat_core.py` 的 `ResonatorNameEnum` 中添加角色：

```python
class ResonatorNameEnum(Enum):
    # ...已有角色...

    # v3.x
    your_character = "你的角色"  # 中文名
```

### 第二步：注册到战斗系统

在 `src/core/combat/combat_system.py` 中：

1. 导入角色类：

```python
from src.core.combat.resonator.your_character import YourCharacter
```

2. 实例化角色：

```python
def __init__(self, ...):
    # ...
    self.your_character = YourCharacter(self.control_service, self.img_service)
```

3. 注册到 `resonator_map`：

```python
self.resonator_map: dict[ResonatorNameEnum, BaseResonator] = {
    # ...已有角色...
    ResonatorNameEnum.your_character: self.your_character,
}
```

### 第三步：测试

1. **训练场测试**：
   - 配置编队包含新角色
   - 启动自动战斗
   - 观察连招是否流畅
   - 检查日志输出的技能检测状态

2. **实战测试**：
   - 在实际 BOSS 战斗中测试
   - 验证各种状态下的连招决策
   - 检查是否有卡顿或空输出

3. **调试技巧**：
   - 查看日志中的 `logger.debug()` 输出
   - 使用 `sleep()` 延长等待时间观察
   - 截图检查坐标和颜色是否正确

---

## 最佳实践

### 1. 命名规范

- **Base 类**: `Base<CharacterName>`
- **实现类**: `<CharacterName>`
- **检测器变量**: `_<feature>_checker`
- **坐标变量**: `_<feature>_point`
- **颜色变量**: `_<feature>_color`

### 2. 日志规范

每个检测方法都应输出日志：

```python
logger.debug(f"{self.resonator_name().value}-共鸣技能: {is_ready}")
```

每个连招片段都应输出日志：

```python
def a4E(self):
    logger.debug("a4E")
    return [...]
```

### 3. 代码组织

建议的文件结构：

```python
# 1. 导入
import ...

# 2. Base 类定义
class BaseYourCharacter(BaseResonator):
    def __init__(...):
        # 2.1 协奏能量
        # 2.2 能量条/特殊状态
        # 2.3 共鸣技能 E
        # 2.4 声骸技能 Q
        # 2.5 共鸣解放 R
        # 2.6 其他特殊检测

    # 2.7 基础方法
    def __str__(...):
    def resonator_name(...):
    def char_class(...):

    # 2.8 检测方法（按技能顺序）
    def energy_count(...):
    def is_concerto_energy_ready(...):
    def is_resonance_skill_ready(...):
    # ...

# 3. 实现类定义
class YourCharacter(BaseYourCharacter):
    # 3.1 COMBO_SEQ 常量
    # 3.2 __init__ 方法
    # 3.3 连招片段方法（从简单到复杂）
    # 3.4 combo() 主逻辑
```

### 4. 性能优化

1. **减少截图次数**：一次截图检测多个状态
2. **合理使用 return**：满足条件后立即 return，避免无效判断
3. **拆分长等待**：提高响应速度和容错性

### 5. 注释规范

```python
# COMBO_SEQ 为训练场单人静态完整连段，后续开发以此为准从中拆分截取
COMBO_SEQ = [...]

def a4E(self):
    """4段普攻接E技能"""
    logger.debug("a4E")
    return [...]
```

---

## 常见问题

### Q1: 技能检测不准确怎么办？

**A**: 检查以下几点：
1. 坐标是否正确（基于 1280×720）
2. 颜色值是否准确（使用取色器重新获取）
3. 是否需要使用 `LogicEnum.AND` 逻辑
4. 容差是否需要调整

### Q2: 连招经常被打断怎么办？

**A**:
1. 拆分长时间等待为多段短等待
2. 在连招片段中多次重复按键（冗余输入）
3. 使用 `combo_action(..., False)` 允许提前切人

### Q3: 如何获取准确的等待时长？

**A**:
1. 在训练场录制完整连招视频
2. 使用视频播放器逐帧分析
3. 计算每个动作的前摇和后摇时间
4. 实战中微调，拆分长等待

### Q4: 如何处理角色的多种状态？

**A**:
1. 为每种状态定义独立的检测器
2. 在 `combo()` 中按优先级检测
3. 为每种状态设计专门的连招片段

### Q5: 能量检测应该返回什么值？

**A**:
- 如果角色有多格能量，返回具体格数（如 0-4）
- 如果只需判断满/空，返回 0/1
- 在 `combo()` 中根据能量值决策连招

### Q6: 如何测试坐标是否正确？

**A**:
1. 在 Base 类的 `__init__` 中打印坐标
2. 使用图像标注工具在截图上标记坐标
3. 临时在 `combo()` 中输出检测结果
4. 使用断点调试查看 `img` 数组的像素值

### Q7: Mornye 的 combo() 现状是什么？

**A**:
Mornye（莫宁）的 `BaseMornye` 实现了完整的双模式能量检测（静质量能 `rest_mass_energy_count()` 和相对动能 `relative_momentum_count()`），但当前 `combo()` 使用与 `GenericResonator` 相同的简单随机打乱逻辑（a4 + random [Eaa, R, z] + Q），尚未利用这些检测功能。定制连招逻辑待后续开发。

---

## 附录：完整示例

参考以下优秀实现：

- **简单角色**: `sanhua.py` - 辅助角色，逻辑简单
- **中等复杂**: `changli.py` - 有能量格检测
- **复杂角色**: `jinhsi.py` - 多阶段 E 技能
- **特殊机制**: `camellya.py` - 变身状态、能量系统
- **双形态**: `cartethyia.py` - 形态切换、复杂决策

---

## 文档维护

如果发现本文档有错误或需要补充，请：

1. 在仓库提 Issue
2. 或直接提交 Pull Request 更新本文档

---

*最后更新: 2026-02-07*
*贡献者: Claude Code Agent*
