# Wuthering Waves Assistant 文档中心

欢迎阅读 WutheringWavesAssistant (WWA) 的技术文档。

## 📚 核心文档

### [ARCH.md](./ARCH.md) - 系统架构文档 ⭐️

**完整的系统架构说明**，包含以下内容：

1. **系统概览** - 项目定位、技术栈、设计理念
2. **项目结构** - 目录布局、模块划分、关键文件说明
3. **架构分层** - 四层架构详解（GUI → Controller → Service → Core）
4. **核心模块** - 战斗系统、BOSS 自动刷取、声骸锁定、OCR/YOLO 识别
5. **数据流** - 从用户操作到游戏控制的完整流程
6. **并发模型** - 多线程战斗、事件驱动暂停/恢复

---

### [CONFIG.md](./CONFIG.md) - 配置参数详解

**配置文件完全指南** (`config.yaml`)，涵盖所有配置节：

- **基础配置** - 游戏路径、模型、OCR、日志
- **游戏崩溃处理** - 定时重启
- **战斗配置** - 最大战斗时间、空闲时间、声骸搜索
- **战斗策略** - FightTactics 连招语法、FightOrder 出战顺序
- **目标 BOSS** - v1.0/v2.0 BOSS 列表

---

### [COMBAT_SYSTEM.md](./COMBAT_SYSTEM.md) - 战斗系统总览

**智能连招系统的完整技术文档**：

- **架构设计** - CombatSystem、BaseResonator、ColorChecker
- **颜色检测机制** - 像素级技能状态识别
- **连招执行引擎** - combo_action 动作序列系统
- **角色分类与排序** - DPS / Support / Healer 优先级
- **编队管理** - 切人逻辑、阵亡处理

---

### [CONTRIBUTING_COMBO.md](./CONTRIBUTING_COMBO.md) - 连招开发贡献指南 ⭐️

**为新角色开发定制连招的完整教程**：

- **开发前准备** - 工具、知识、文件结构
- **Base 类开发** - 技能检测器定义、坐标获取、检测方法实现
- **连招实现类开发** - 动作序列、连招片段、combo() 主逻辑
- **注册与测试** - 枚举添加、系统注册、测试方法
- **最佳实践** - 命名规范、代码组织、性能优化
- **常见问题** - FAQ 和调试技巧

---

## 🎮 角色连招文档

每个定制连招角色都有独立的详细分析文档：

| 角色 | 文档 | 定位 | 属性 |
|------|------|------|------|
| 椿 (Camellya) | [camellya.md](./resonators/camellya.md) | 主C | 湮灭 |
| 坎特蕾拉 (Cantarella) | [cantarella.md](./resonators/cantarella.md) | 辅助 | 湮灭 |
| 卡提希娅 (Cartethyia) | [cartethyia.md](./resonators/cartethyia.md) | 主C | 气动 |
| 长离 (Changli) | [changli.md](./resonators/changli.md) | 副C | 熔融 |
| 夏空 (Ciaccona) | [ciaccona.md](./resonators/ciaccona.md) | 辅助 | 气动 |
| 安可 (Encore) | [encore.md](./resonators/encore.md) | 主C | 熔融 |
| 今汐 (Jinhsi) | [jinhsi.md](./resonators/jinhsi.md) | 主C | 衍射 |
| 琳奈 (Lynae) | [lynae.md](./resonators/lynae.md) | 辅助 | 衍射 |
| 莫宁 (Mornye) | [mornye.md](./resonators/mornye.md) | 治疗 | 熔融 |
| 菲比 (Phoebe) | [phoebe.md](./resonators/phoebe.md) | 辅助 | 衍射 |
| 弗洛洛 (Phrolova) | [phrolova.md](./resonators/phrolova.md) | 主C | 熔融 |
| 漂泊者 (Rover) | [rover.md](./resonators/rover.md) | 副C | 通用 |
| 散华 (Sanhua) | [sanhua.md](./resonators/sanhua.md) | 辅助 | 冷凝 |
| 守岸人 (Shorekeeper) | [shorekeeper.md](./resonators/shorekeeper.md) | 治疗 | 衍射 |
| 维里奈 (Verina) | [verina.md](./resonators/verina.md) | 治疗 | 衍射 |
| 通用角色 (Generic) | [generic.md](./resonators/generic.md) | 副C | 通用 |

---

## 🚀 快速开始

### 用户使用

1. **了解系统** → 阅读 [ARCH.md](./ARCH.md) 了解整体架构
2. **配置项目** → 参考 [CONFIG.md](./CONFIG.md) 和 `config.yaml`
3. **战斗系统** → 阅读 [COMBAT_SYSTEM.md](./COMBAT_SYSTEM.md) 了解连招机制
4. **角色详情** → 查看 [resonators/](./resonators/) 目录下各角色文档

### 开发贡献

1. **连招开发** → 阅读 [CONTRIBUTING_COMBO.md](./CONTRIBUTING_COMBO.md) 学习如何为新角色开发定制连招
2. **参考实现** → 查看 [resonators/](./resonators/) 目录下的角色文档作为示例
3. **测试验证** → 在训练场和实战中测试连招效果

---

*最后更新: 2026-02-07*
