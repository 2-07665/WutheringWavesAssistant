# 弗洛洛 (Phrolova) - 连招逻辑分析

## 基本信息

| 属性 | 值 |
|------|------|
| 角色名称 | 弗洛洛 (Phrolova) |
| 角色定位 | MainDPS（主输出） |
| 元素属性 | 湮灭 (Havoc) |
| 协奏类型 | 紫圈 (concerto_havoc) |
| 版本 | v2.5 |
| 源文件 | `src/core/combat/resonator/phrolova.py` |

## 角色机制

弗洛洛拥有**乐声**系统：

- 通过普攻、E 技能产生乐声（弦乐/管乐/彩乐）
- 检测乐声数量（最多6个检测点）
- 共鸣解放进入特殊状态（谢幕指令）

## 技能状态检测

`BasePhrolova` 中实现了完整的技能检测：

### 乐声检测

| 检测项 | 检测方式 | 说明 |
|--------|----------|------|
| 乐声1-6 | 弦乐/管乐/彩乐三种颜色 | 检测6个位置的乐声存在 |

乐声颜色（BGR）：
- 弦乐 (strings): `(28,14,176)`, `(26,15,134)`, `(29,19,149)`
- 管乐 (winds): `(181,28,45)`, `(138,36,52)`
- 彩乐 (cadenza): `(65,53,143)`, `(59,53,102)`

### 技能检测

| 检测项 | 图标颜色 | 逻辑 | 说明 |
|--------|----------|------|------|
| 普攻·生与死的乐章 | 白色 `(255,255,255)` | AND | 普攻形态1 |
| 普攻·亡与死的乐章 | 白色 `(255,255,255)` | AND | 普攻形态2 |
| 共鸣技能·稍纵即逝的梦呓 | 白色 `(255,255,255)` | AND | E技能形态1 |
| 共鸣技能·永不消逝的梦呓 | 白色 `(255,255,255)` | AND | E技能形态2 |
| 声骸技能 | 白色 `(255,255,255)` | AND | 声骸就绪 |
| 共鸣解放 | 白色 `(255,255,255)` | AND | 大招就绪 |
| 共鸣解放 指令·谢幕 | R+普攻同时就绪 | AND | 谢幕指令可用 |

## 当前实现状态

```python
class Phrolova(BasePhrolova):
```

弗洛洛继承自 `BasePhrolova`，拥有完整的技能检测能力，但当前 `combo()` 使用与 `GenericResonator` 相同的简单随机打乱逻辑，尚未利用 `BasePhrolova` 中的状态检测功能。

## 连招片段

| 方法 | 描述 | 说明 |
|------|------|------|
| `a4()` | 4段普攻 | 4次快速普攻 |
| `Eaa()` | E+2段普攻 | E技能接两段普攻 |
| `E()` | E技能 | 单独E技能 |
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

当前逻辑与 GenericResonator 相同：a4 + 随机打乱 [Eaa, R, z] + Q。

## exit_special_state()

`exit_special_state()` 用于在声骸搜索前退出大招状态：

```python
def exit_special_state(self, scenario_enum):
    if scenario_enum != ScenarioEnum.BeforeEchoSearch:
        return
    img = self.img_service.screenshot()
    if not self.is_cue_curtain_call_ready(img):
        return
    # 按R退出大招状态（R落地 2.37秒）
    quit_seq = [["R", 0.05, 2.37]]
    self.combo_action(quit_seq, True, ignore_event=True)
```

## 设计分析

### 当前状态

弗洛洛已注册到 `resonator_map`，继承 `BasePhrolova`。`BasePhrolova` 中实现了完整的乐声检测和多种技能检测，但 `combo()` 尚未利用这些检测能力。

### 后续开发方向

建议基于 `BasePhrolova` 的检测方法开发智能连招：

1. 利用 `volatile_note_count()` 检测乐声数量
2. 区分两种普攻和两种E技能形态
3. 利用 `is_cue_curtain_call_ready()` 检测谢幕指令
4. 管理共鸣解放的定音 CD（24秒）

---

*最后更新: 2026-02-07*
