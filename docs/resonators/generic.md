# 通用角色 (Generic) - 连招逻辑分析

## 基本信息

| 属性 | 值 |
|------|------|
| 角色名称 | generic（通用） |
| 角色定位 | SubDPS（副输出） |
| 元素属性 | 无 |
| 协奏类型 | 无（不检测） |
| 源文件 | `src/core/combat/resonator/generic.py` |
| 适用对象 | 未注册定制连招的所有角色 |

## 概述

`GenericResonator` 是所有未注册定制连招角色的默认实现。当编队中出现 `resonator_map` 中没有的角色时，系统自动使用此通用连招。

## 技能状态检测

通用角色**不检测任何技能状态**，仅依赖固定的按键序列。

## 连招片段

| 方法 | 描述 | 说明 |
|------|------|------|
| `a4()` | 4段普攻 | 4次快速普攻 |
| `Eaa()` | E+2段普攻 | E技能接两段普攻 |
| `E()` | E技能 | 单独的E技能 |
| `z()` | 重击 | 长按0.50秒 |
| `Q()` | 声骸技能 | 声骸释放 |
| `R()` | 共鸣解放 | 大招 |

### COMBO_SEQ（训练场连段参考）

```python
COMBO_SEQ = [
    ["a", 0.05, 0.30],  # 普攻×4
    ["a", 0.05, 0.30],
    ["a", 0.05, 0.30],
    ["a", 0.05, 0.30],
    ["z", 0.50, 0.50],  # 重击
    ["R", 0.05, 0.50],  # 大招
    ["Q", 0.05, 0.50],  # 声骸
]
```

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

## 适用角色

以下角色在编队中使用通用连招：

- 菲比 (Phoebe) - 虽有 BasePhoebe，但未注册到 `resonator_map`，且 `combo()` 为空实现
- 所有其他未注册角色

> **注意**：漂泊者 (Rover) 虽不在 `resonator_map` 中，但 `set_resonators()` 对其做了特殊处理，直接使用 `Rover` 实例及其自身的 `combo()`，不会回退到 GenericResonator。详见 [rover.md](rover.md)。

## 设计特点

1. **通用兼容** - 对所有角色都能工作的最简连招
2. **随机打乱** - Eaa/R/z 三个技能随机排列，避免固定模式
3. **安全回退** - 作为所有未定制角色的后备方案
4. **无状态检测** - 不截图不检测，纯固定序列执行

---

*最后更新: 2026-02-07*
