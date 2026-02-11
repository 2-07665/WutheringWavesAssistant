# 配置参数详解

本文档详细说明 `config.yaml` 中所有可配置参数的含义、默认值和调优建议。

## 1. 脚本基础配置

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `AppPath` | string | 空 | 游戏路径，默认从注册表读取。路径使用 `\\` 分隔。示例：`D:\\Wuthering Waves\\Wuthering Waves Game\\Wuthering Waves.exe` |
| `ModelName` | string | `"yolo"` | 目标检测模型名称，已实现自动匹配声骸模型 |
| `OcrInterval` | int | `0` | OCR 识别间隔时间（秒） |
| `GameMonitorTime` | int | `5` | 游戏窗口检测间隔时间（秒） |
| `LogFilePath` | string | 空 | 日志保存路径，留空为项目根目录。示例：`c:\\mc_log.txt` |

## 2. 游戏崩溃捕获及处理

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `RestartWutheringWaves` | bool | `false` | 是否定时重启游戏 |
| `RestartWutheringWavesTime` | int | `7200` | 重启间隔时间（秒），仅当 `RestartWutheringWaves` 为 `true` 时生效 |

## 3. 控制台信息

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `EchoDebugMode` | bool | `true` | 声骸锁定功能 DEBUG 显示输出开关 |
| `EchoSynthesisDebugMode` | bool | `true` | 声骸合成锁定功能 DEBUG 显示输出开关 |

## 4. 自动战斗及声骸锁定配置

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `MaxFightTime` | int | `120` | 单次战斗最大时间（秒），超时进行下一目标 |
| `MaxIdleTime` | int | `12` | 战斗完成后的空闲时间（秒），不能小于 5 |
| `MaxSearchEchoesTime` | int | `18` | 战斗后搜索声骸最大时间（秒），与 `MaxIdleTime/2` 取较大值 |
| `SelectRoleInterval` | int | `2` | 选择角色的时间间隔（秒），最小为 2 |
| `DungeonWeeklyBossLevel` | int | `40` | 周本 BOSS 最低等级（当前索拉等级×10） |
| `CharacterHeal` | bool | `true` | 是否判断角色阵亡并返回神像复活。需确保背包有复活药剂 |
| `SearchEchoes` | bool | `true` | 是否搜索声骸 |
| `SearchDreamlessEchoes` | bool | `true` | 是否搜索无妄者声骸 |
| `EchoLock` | bool | `true` | 是否启用声骸锁定功能 |
| `EchoMaxContinuousLockQuantity` | int | `25` | 最大连续检测到已锁定声骸的数量，超过则停止 |

## 5. 战斗策略 (FightTactics)

### 5.1 语法说明

`FightTactics` 定义了三个角色的释放技能顺序，每行对应一个角色的连招序列：

```yaml
FightTactics:
    - "q~0.1,e~0.1,a"       # 角色1
    - "r,q~0.1,e,a,a,a,a~,e" # 角色2
    - "q~0.1,e,r,e,a,a,a,a,a,e,a,a,a,a,a,e" # 角色3
```

### 5.2 按键说明

| 按键 | 说明 |
|------|------|
| `a` | 普攻（默认连点 0.3 秒） |
| `a~0.5` | 普攻按下 0.5 秒 |
| `a(0.5)` | 连续普攻 0.5 秒 |
| `e` | 共鸣技能 |
| `e~0.1` | 共鸣技能短按 0.1 秒 |
| `q` | 声骸技能 |
| `q~0.1` | 声骸技能短按 0.1 秒（摩托车短按） |
| `r` | 共鸣解放 |
| `s` | 重击 |
| `l` | 向后闪避（小写 L） |
| 数字 | 间隔时间（秒） |

> **注意**：`FightTactics` 是由 `page_event_service.py` 解析和执行的独立战斗路径。当角色已在 `resonator_map` 中注册定制连招时，系统使用该角色 `combo()` 方法中的连招逻辑，`FightTactics` 不参与。

## 6. 战斗顺序 (FightOrder)

```yaml
FightOrder: [1, 2, 3]
```

- 数字对应角色在编队中的位置（1-3）
- 修改顺序可改变出战优先级
- 示例：`[3, 1, 2]` 先让 3 号位出手
- **注意**：`FightTactics` 中的连招行也需要对应调整顺序

## 7. 目标 BOSS (TargetBoss)

```yaml
TargetBoss:
    # =========== v1.0 boss ===========
    - "无妄者"
    #- "无归的谬误"
    # ...
    # =========== v2.0 boss ===========
    #- "异构武装"
    # ...
```

- 取消行首 `#` 号即可启用该 BOSS
- 每行前面必须有 4 个空格
- 无特殊要求建议单刷无妄者
- v1.0/v2.0 BOSS 需在 2.0 版本后手打一次解锁附近传送

---

*最后更新: 2026-02-06*
