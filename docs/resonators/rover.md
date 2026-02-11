# 漂泊者 (Rover) - 连招逻辑分析

## 基本信息

| 属性 | 值 |
|------|------|
| 角色名称 | 漂泊者 (Rover) |
| 角色定位 | SubDPS（副输出） |
| 元素属性 | 通用 |
| 协奏类型 | 无（未实现检测） |
| 版本 | 常驻 |
| 源文件 | `src/core/combat/resonator/rover.py` |
| 注册状态 | ✅ `set_resonators()` 中直接引用（非 `resonator_map`） |

## 角色机制

漂泊者是玩家角色，无特殊机制。`BaseRover` 是最简单的角色基类实现，没有任何技能状态检测。

## 技能状态检测

`BaseRover` **不包含任何技能状态检测**，仅继承 `BaseResonator` 的基本接口。

## 连招片段

| 方法 | 描述 | 说明 |
|------|------|------|
| `a4()` | 4段普攻 | 每段0.30秒间隔 |
| `a2()` | 2段普攻 | 快速两段 |
| `Eaa()` | E+2段普攻 | E接两段普攻 |
| `E()` | E技能 | 单独E，等待0.50秒 |
| `z()` | 重击 | 长按0.50秒 |
| `Q()` | 声骸技能 | 声骸释放 |
| `R()` | 共鸣解放 | 大招 |
| `full_combo()` | 完整连段 | 测试用，返回 COMBO_SEQ |

## 连招决策逻辑 (`combo()`)

漂泊者的 `combo()` 使用固定序列，不依赖截图检测：

```python
def combo(self):
    self.combo_action(self.a2(), True)     # 2段普攻
    self.combo_action(self.Eaa(), True)    # E+2段普攻
    self.combo_action(self.z(), False)     # 重击
    self.combo_action(self.a2(), True)     # 2段普攻
    self.combo_action(self.R(), False)     # 大招
    self.combo_action(self.Q(), False)     # 声骸
```

固定循环：a2 → Eaa → z → a2 → R → Q

## 设计特点

1. **无智能决策** - 不检测任何技能状态，按固定顺序释放
2. **最简实现** - 作为基础参考实现，展示连招框架的使用方式
3. **特殊注册** - 虽不在 `resonator_map` 中，但 `set_resonators()` 对漂泊者做了特殊处理，直接使用 `self.rover` 实例，**会执行自身的 combo()**
4. **固定节奏** - 所有动作间隔统一为 0.30-0.50 秒

---

*最后更新: 2026-02-06*
