# 坎特蕾拉 (Cantarella) - 连招逻辑分析

## 基本信息

| 属性 | 值 |
|------|------|
| 角色名称 | 坎特蕾拉 (Cantarella) |
| 角色定位 | Support（辅助） |
| 元素属性 | 湮灭 (Havoc) |
| 协奏类型 | 紫圈 (concerto_havoc) |
| 版本 | v2.2 |
| 源文件 | `src/core/combat/resonator/cantarella.py` |

## 角色机制

坎特蕾拉的 `BaseCantarella` 中定义了协奏能量检测（紫圈），但能量格数检测、共鸣技能、声骸技能、共鸣解放的检测方法均已被注释掉，尚未启用。

## 技能状态检测

### 已初始化（检测器对象已创建）

| 检测项 | 检测方式 | 说明 |
|--------|----------|------|
| 协奏能量 | `concerto_havoc()` 紫圈 | 检测器已创建，但 `is_concerto_energy_ready()` 方法被注释 |

### 已注释（待启用）

| 检测项 | 说明 |
|--------|------|
| 协奏能量检测方法 | `is_concerto_energy_ready()` 方法被注释 |
| 能量1-4格 | 血条上方4格能量条 |
| 共鸣技能 E | E技能就绪 |
| 声骸技能 Q | 声骸就绪 |
| 共鸣解放 R | 大招就绪 |

## 连招片段

| 方法 | 描述 | 说明 |
|------|------|------|
| `a2()` | 2段普攻 | 快速两段 |
| `a3()` | 3段普攻 | 三段普攻 |
| `a4()` | 4段普攻 | 四段普攻 |
| `Eaa()` | E+2段普攻 | E技能接两段普攻 |
| `E()` | E技能 | 单独E技能 |
| `z()` | 重击 | 长按0.50秒 |
| `Q()` | 声骸技能 | 声骸释放 |
| `R()` | 共鸣解放 | 大招 |

## 连招决策逻辑 (`combo()`)

```python
def combo(self):
    self.combo_action(self.a3(), True)
    self.combo_action(self.R(), False)
    if self.random_float() < 0.66:
        self.combo_action(self.z(), True)
        if self.random_float() < 0.66:
            self.combo_action(self.z(), False)
        self.combo_action(self.E(), False)
        if self.random_float() < 0.66:
            self.combo_action(self.a3(), True)
        else:
            self.combo_action(self.a4(), True)
    else:
        self.combo_action(self.a3(), True)
    self.combo_action(self.E(), False)
    self.combo_action(self.Q(), False)
```

```
1. a3() 三段普攻
2. R() 尝试大招
3. 66%概率进入重击分支:
   ├─ z() 重击
   ├─ 66%概率再 z() 一次
   ├─ E() 技能
   └─ 66%概率 a3() / 34%概率 a4()
4. 34%概率仅 a3()
5. E() 技能
6. Q() 声骸
```

## 设计特点

1. **随机分支** - 使用 `random_float()` 在多处引入随机性，避免固定模式
2. **无状态检测** - 不依赖截图检测，按固定流程+随机分支执行
3. **已注册** - 已注册到 `resonator_map`，使用自己的 `combo()` 方法
4. **检测待开发** - `BaseCantarella` 中的能量和技能检测已定义但被注释，待后续启用

---

*最后更新: 2026-02-07*
