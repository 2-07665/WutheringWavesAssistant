# 莫宁 (Mornye) - 连招逻辑分析

## 基本信息

| 属性 | 值 |
|------|------|
| 角色名称 | 莫宁 (Mornye) |
| 角色定位 | Healer（治疗） |
| 元素属性 | 熔融 (Fusion) |
| 协奏类型 | 红圈 (concerto_fusion) |
| 版本 | v3.0 |
| 源文件 | `src/core/combat/resonator/mornye.py` |

## 角色机制

莫宁拥有**双模式**战斗系统：

### 基准模式（常规形态）

- **静质量能** - 能量条，满时可重击进入广域观测模式
- 3段普攻积攒能量
- E技能（期望误差）
- 重击·位势转换：满能量时重击进入蝴蝶形态

### 广域观测模式（蝴蝶形态）

- **相对动能** - 能量条，满时可释放重击·反演
- 普攻和E技能为变身后的强化版
- E技能·分布式阵列
- 重击·反演：消耗相对动能

### 进阶轴核心循环

1. 3段普攻攒4格能量
2. 重击进入蝴蝶
3. E退出蝴蝶（获得5格能量）
4. 跳+普攻清空能量
5. 声骸技能合轴

## 技能状态检测

### 能量检测

| 检测项 | 值 | 说明 |
|--------|------|------|
| 静质量能 20% | 蓝色 `(63,119,250)` | 基准模式能量 |
| 静质量能 50% | 蓝色 | 基准模式能量 |
| 静质量能 80% | 蓝色 | 基准模式能量 |
| 相对动能 20% | 暖色系 | 广域观测模式能量 |
| 相对动能 50% | 暖色系 | 广域观测模式能量 |
| 相对动能 80% | 暖色系 | 广域观测模式能量 |

### 状态检测

| 检测项 | 逻辑 | 说明 |
|--------|------|------|
| 重击·位势转换 | AND | 满能量可变身（4个检测点白色） |
| 广域观测模式 | AND | 是否在蝴蝶形态（4个检测点白色） |
| 共鸣技能·分布式阵列 | AND | 蝴蝶E技能 |
| 重击·反演 | AND | 蝴蝶重击（5个检测点白色） |
| 声骸技能 Q | OR | 声骸就绪 |
| 共鸣解放 R | AND | 大招就绪 |
| 共鸣解放2 | AND | 谐振场内大招 |

## 连招片段

| 方法 | 描述 | 说明 |
|------|------|------|
| `a4()` | 4段普攻 | 4次快速普攻 |
| `Eaa()` | E+2段普攻 | E技能接两段普攻 |
| `E()` | E技能 | 单独的E技能 |
| `z()` | 重击 | 长按0.50秒 |
| `Q()` | 声骸技能 | 声骸释放 |
| `R()` | 共鸣解放 | 大招 |

## 连招决策逻辑 (`combo()`)

```python
def combo(self):
    self.combo_action(self.a4(), False)

    combo_list = [self.Eaa(), self.R(), self.z()]
    random.shuffle(combo_list)
    for i in combo_list:
        self.combo_action(i, False)
        time.sleep(0.15)

    self.combo_action(self.Q(), False)
```

1. 先打 a4() 四段普攻
2. 随机打乱 [Eaa, R, z] 的顺序并依次执行
3. 最后释放声骸 Q()

> **注意**：虽然 `BaseMornye` 中实现了完整的状态检测方法（静质量能、相对动能、广域观测模式等），但当前 `combo()` 并未使用这些检测功能，而是采用与 `GenericResonator` 相同的简单随机打乱逻辑。定制连招逻辑尚待开发。

## exit_special_state()

`exit_special_state()` 方法用于在声骸搜索前退出广域观测模式（蝴蝶形态）：

```python
def exit_special_state(self, scenario_enum):
    if scenario_enum != ScenarioEnum.BeforeEchoSearch:
        return
    img = self.img_service.screenshot()
    if not self.is_wide_field_observation_mode_ready(img):
        return
    # 跳跃退出蝴蝶形态
    quit_seq = [["j", 0.05, 2.00]]
    self.combo_action(quit_seq, True, ignore_event=True)
```

## 设计特点

1. **丰富的状态检测** - `BaseMornye` 实现了完整的双模式能量检测，为后续定制连招做准备
2. **简单的连招执行** - 当前 `combo()` 使用简单随机打乱，与 GenericResonator 逻辑相同
3. **蝴蝶退出保护** - `exit_special_state()` 在声骸搜索前检测并退出广域观测模式
4. **已注册** - 莫宁已注册到 `resonator_map`，使用自己的 `combo()` 方法

---

*最后更新: 2026-02-07*
