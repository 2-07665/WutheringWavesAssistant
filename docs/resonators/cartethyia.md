# 卡提希娅 (Cartethyia) - 连招逻辑分析

## 基本信息

| 属性 | 值 |
|------|------|
| 角色名称 | 卡提希娅 (Cartethyia) |
| 角色定位 | MainDPS（主输出） |
| 元素属性 | 气动 (Aero) |
| 协奏类型 | 绿圈 (concerto_aero) |
| 版本 | v2.4 |
| 源文件 | `src/core/combat/resonator/cartethyia.py` |

## 角色机制

卡提希娅拥有独特的**双形态**系统：

- **小卡（卡提希娅本体）** - 常态形态，召唤三把剑
- **大卡（芙露德莉斯）** - 变身形态，通过 R 变身

### 三剑系统

小卡可以召唤三把剑，收剑时产生伤害：
- **异权剑（剑一）** - 通过重击召唤
- **神权剑（剑二）** - 通过普攻第四段召唤
- **人权剑（剑三）** - 通过E技能召唤

### 形态切换

- **小卡→大卡**: R（听骑士从心祈愿）进入芙露德莉斯形态
- **大卡→化身小卡**: R（化身·芙露德莉斯→化身·卡提希娅）
- **化身小卡→大卡**: R（化身·卡提希娅→芙露德莉斯）

### 风蚀效应

- 持续16秒，超时清空
- 普攻第四段叠一层
- E技能叠两层
- 变奏叠两层

## 技能状态检测

### 小卡技能

| 检测项 | 逻辑 | 说明 |
|--------|------|------|
| 共鸣技能 - 小卡E | AND | 卡提希娅的E技能 |
| 声骸技能 | OR | 声骸就绪 |
| 共鸣解放 R | AND | 听骑士从心祈愿 |

### 大卡技能

| 检测项 | 逻辑 | 说明 |
|--------|------|------|
| 共鸣技能 E1 - 芙露德莉斯 | AND | 此剑为潮浪之意 |
| 共鸣技能 E2 - 芙露德莉斯 | AND | 凭风斩浪破敌 |
| 化身·芙露德莉斯 | AND | R图标显示大卡形态 |
| 化身·卡提希娅 | AND | R图标显示小卡形态 |
| 看潮怒风哮之刃 | AND | 大卡大招可释放 |

### 状态识别

| 检测项 | 逻辑 | 说明 |
|--------|------|------|
| 异权剑（剑一） | AND | 重击剑是否存在 |
| 神权剑（剑二） | OR | 普攻剑是否存在 |
| 人权剑（剑三） | OR | E技能剑是否存在 |
| 显化 | AND | 大卡显化状态 |
| 决意 | OR | 大卡血条上方能量条 |

### 运行时动态变量

```python
is_avatar_cartethyia_attack_done = False  # 化身·小卡是否已打过一套攻击
```

## 连招片段

### 小卡片段

| 方法 | 描述 |
|------|------|
| `cartethyia_a4()` | 小卡4段普攻，召唤神权剑 |
| `cartethyia_a2_start()` | 普攻前两下 |
| `cartethyia_a2_end()` | 普攻后两下 |
| `cartethyia_a4Eza()` | 4段普攻+E+重击+普攻 |
| `cartethyia_Ea()` | E+普攻，召唤人权剑 |
| `cartethyia_Eza()` | E+重击+普攻 |
| `cartethyia_E()` | 仅E技能 |
| `cartethyia_z()` | 重击，召唤异权剑 |
| `cartethyia_ja()` | 下落攻击收剑 |
| `cartethyia_R()` | 小卡R变身大卡 |

### 大卡片段

| 方法 | 描述 |
|------|------|
| `fleurdelys_a5()` | 大卡5段普攻 |
| `fleurdelys_a2()` | 大卡前2段普攻 |
| `fleurdelys_EaaEaaa()` | 大卡双E连招 |
| `fleurdelys_EaaE()` | 大卡E+普攻+E |
| `fleurdelys_za_a3()` | 大卡重击派生射箭+起飞+空中2a |
| `fleurdelys_ja2()` | 大卡空中2段普攻 |
| `fleurdelys_ja3()` | 大卡空中3段普攻 |
| `fleurdelys_R_blade_of_howling_squall()` | 大卡大招：看潮怒风哮之刃 |

### 形态切换

| 方法 | 描述 |
|------|------|
| `avatar_cartethyia_to_fleurdelys_Ra3()` | 化身小卡切大卡+普攻 |
| `fleurdelys_to_avatar_cartethyia_Ra3()` | 大卡切化身小卡+普攻 |

## 连招决策逻辑 (`combo()`)

```
入场: a3() 打几下普攻

截图检测所有技能和状态

1. 化身·芙露德莉斯大招就绪（看潮怒风哮之刃）:
   ├─ 释放大招 fleurdelys_R_blade_of_howling_squall()
   ├─ 检查boss血量
   └─ 若小卡E就绪 → Q + cartethyia_a4() + cartethyia_Eza()
   └─ return

2. 释放声骸 Q

3. 化身·卡提希娅状态:
   ├─ 有E → cartethyia_a4() + cartethyia_Eza()
   ├─ 无E → cartethyia_a4()
   ├─ 首次攻击 → 标记完成，等待合轴
   └─ 非首次 → 标记需要切换形态

4. 化身·芙露德莉斯 或 需要切换:
   ├─ 需要切换 → avatar_to_fleurdelys_Ra3() 或 R()
   │   └─ fleurdelys_EaaE()
   ├─ 有E → fleurdelys_EaaE()
   ├─ 无E → fleurdelys_ja3()
   └─ 检查大招 → 有则释放 + 小卡E/三剑补充

5. 常态小卡（有E或R）:
   ├─ 有R → 补满三剑（a4+Eza+z+ja）
   ├─ 无R → 打普攻连 + 检查E
   ├─ 检查R → 有R则 cartethyia_R() 变身
   └─ 大卡出场 → fleurdelys_EaaE() 或 fleurdelys_ja3()

6. 兜底 → cartethyia_a4()
```

## 设计特点

1. **双形态动态切换** - 程序需要追踪当前是小卡还是大卡状态
2. **三剑收集** - 需要检测三把剑的存在状态，有大招时优先补满三剑
3. **运行时状态变量** - `is_avatar_cartethyia_attack_done` 跟踪化身小卡的攻击状态
4. **Boss 血量判断** - 多处检查 Boss 血量 ≤ 0.01 提前结束，避免空输出

---

*最后更新: 2026-02-07*
