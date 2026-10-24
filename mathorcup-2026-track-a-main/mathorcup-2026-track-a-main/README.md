# MathorCup 2026 赛道 A

B/C阶段交付与后续任务统一走[GitHub交接流程](docs/GITHUB_HANDOFF.md)：提交`[待验收]`PR，读取总控的验收/续派评论，无需队长转发。当前为A回报时一并收件，未启用GitHub事件直接唤醒。

三人协作项目。当前处于数据语义核验与探索性基线阶段；初赛截止为 **2026-10-30 20:00（北京时间）**。现阶段按分工推进，比赛成果稳定后再统一整理完整项目。

| 工作入口 | 成员 | 责任 |
|---|---|---|
| [A 主线](workstreams/A-main/README.md) | 本项目用户 / Codex Pro | 实现、实验、整合 |
| [B 证据](workstreams/B-liuyuan/README.md) | 刘源 / DeepSeek | 来源、尺度、单位与科学解释 |
| [C 验收](workstreams/C-xiexiaoyu/README.md) | 谢小鱼 / Codex Plus | 独立复现、结论证据与交付 |

## 开始工作

1. 阅读 [总控状态](CONTROL.md) 与 [统一工作规范](docs/TEAM_PROTOCOL.md)。
   所有成员必须执行[工具工作流](docs/TOOL_WORKFLOW.md)，不能用纯AI问答代替实际核验和实验。
2. 按职责阅读 [B 长期任务](docs/tasks/B_LONG_TERM.md)、[C 长期任务](docs/tasks/C_LONG_TERM.md)，或主线实现聊天中的任务。
3. 了解 [整体架构链路](docs/ARCHITECTURE.md) 和 [GitHub 协作与权限](docs/GITHUB_COLLABORATION.md)。
4. 本机原始数据位于 `D:\MathorCup`。其他成员通过本地配置指定自己的数据路径，不应修改原文件或硬编码队友电脑路径。

实现和运行命令见 [A运行说明](docs/A_RUNBOOK.md)，首轮真实运行的[轻量证据](reports/A/phase1/README.md)已整理。首次运行前检查对应实验的数据、代码及验证版本；A已同环境复跑，C独立验收尚待进行。

## 已有证据

- [初步数据核查](research/data-audit.md)
- [前期调研与作战方案](作战方案-v0.1.md)
- [评分来源追溯](research/scoring-scale-investigation.md)
- [目标与单位核验](research/target-unit-findings.md)、[目标字典](research/target-dictionary.csv)、[单位字典](research/chemical-units.csv)

## 协作方式

每人长期负责一条工作线，按里程碑交付，不逐条转发聊天。比赛期间每日（含周末）更新一次本人成员状态，约定默认北京时间 **21:00 前**；这是一项人工协作约定，不代表已设置自动提醒。首个证据/复现里程碑建议在收到任务后的 24 小时内交付。重大口径错误或数据泄漏立即上报。

仓库建好后以 PR、提交版本和状态文件为交接载体；建库前将相同目录结构打包交接。总控不会自动看到 B/C 的账号聊天，也不会在无人触发时持续监视 GitHub。成员只需在里程碑发送一次“PR/文件路径 + 关键结论”，总控读取实际文件验收。

## 仓库身份

已创建个人私有仓库 [echo1229/mathorcup-2026-track-a](https://github.com/echo1229/mathorcup-2026-track-a)。仓库Owner为echo1229；每位成员使用本人获授权的账号协作，不能共享账号。总控当前操作身份已核验为echo1229。刘源账号为Forever-lyy1012；谢小鱼账号为gsgvrv7dn8-netizen。两人的write权限邀请已发送，接受状态见CONTROL。
