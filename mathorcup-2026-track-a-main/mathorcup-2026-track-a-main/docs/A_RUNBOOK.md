# A 主线探索工程：复现说明

本工程由 AI 辅助实现，用于检查数据与实验流水线。模型、固定参数、验证及指标仍待队员实质确认，不是官方最终结果，也不表示已满足独立建模要求。

## 实际采用的技能、工具与证据

按[工具驱动工作流](TOOL_WORKFLOW.md)执行。本阶段已经通过终端读取 `C:\Users\61571\.agents\skills\ecc\mle-workflow\SKILL.md`，来源为本机ECC技能目录，技能文件未声明版本号，版本记为unknown；实际采用数据契约、折内处理、可追溯评估与轻量运行记录。

| 已实际执行 | 具体操作与结果 | 现有证据 |
|---|---|---|
| 环境与工作区检查 | PowerShell/Python检查解释器和已安装包；`rg`定位工程文件；`git status`、HEAD及作用域内diff检查 | [首跑manifest](../runs/A-20261024-001/manifest.json)的environment/code字段；终端原始输出在A聊天工具记录 |
| 数据操作 | Python/pandas读取真实1/4.csv；唯一beer一对一对齐、字段/风格/缺失/数值校验，得到250×231/250×50 | [数据审计](../runs/A-20261024-001/data_audit.json)、[数据实现](../src/mathorcup_a/data.py) |
| 必要测试 | `python -m pytest -q`，最后一次完整运行49 passed、6.86秒 | [测试目录](../tests/)、首跑source_snapshot内相同测试源码；执行输出在A聊天工具记录，未另存pytest.log |
| 真实训练与评估 | scikit-learn训练均值及固定Ridge，两个完整命令见下文及manifest.argv | [首跑manifest](../runs/A-20261024-001/manifest.json)、[实际执行日志](../runs/A-20261024-001/execution_log.jsonl)、[逐目标指标](../runs/A-20261024-001/target_metrics.csv) |
| 同环境复跑与产物核查 | 独立新run_id重新执行相同代码/数据/配置；核心产物哈希一致；从OOF另行重算指标 | [复跑manifest](../runs/A-20261024-002/manifest.json)、[复跑日志](../runs/A-20261024-002/execution_log.jsonl)、[核查记录](../runs/A-20261024-phase1-audit.json) |
| AI工程审查 | code-reviewer/python-reviewer实际检查并反馈；修复CSV行宽、常数小数R²及安装入口边界，最终复查通过 | [AI过程记录](../records/ai/A/20261024-baseline-engineering.md)及A聊天协作agent消息；不等于谢小鱼独立验收 |

能力限制：本机CIM内存查询不可用，已记录但不影响本轮CPU运行；没有另建或验证全新虚拟环境。A本阶段对科学来源的使用限于读取项目证据文件，不冒称由A完成浏览器文献追溯。关键终端输出与审查交互保留在本聊天，完整聊天导出尚待正式AI说明汇总。未经实际执行的后续建模/科学解释仍为待验证。

## 当前边界

- 只读取附件 `1.csv` 的231个化学/理化特征与 `4.csv` 的50个已观测标准化感官目标。
- 以字符串 `beer` 唯一键显式对齐，要求键集合完全一致、风格一致；`beer_id`不参与连接，元数据不作模型特征。
- 不使用空白评分卡 `3.xlsx`；不使用附件2/5/6/7/8、既有重要性或SHAP筛选特征。
- 不反变换为0–6，不做物理单位逆变换、缺陷阈值判断、Top-3解释或生成/迁移。
- 已读统一规范v1与新增尺度/单位证据：4.csv与来源论文S4全部250×50数值一致，先逐品鉴者标准化再汇总；26项numeric、24项继承父组强度的子描述均暂作为已观测连续目标。子描述不视为独立滑杆或现成二分类标签。3.xlsx的barnyard错误summary引用不进入本工程。

## 环境与安装

已检查本机 Windows、Python 3.12.0、12个逻辑CPU；内存查询被当前CIM权限限制，尚未核实可用内存。当前依赖已安装，不需安装即可运行。`requirements.txt`固定本轮直接依赖及运行时传递依赖；每次运行另记录实际Python、包版本与BLAS库信息。执行入口为仓库脚本，不提供普通包安装后的控制台命令。

在项目目录使用 PowerShell：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

独立环境需要可用网络/本地包缓存；本阶段没有实际创建或验证新的虚拟环境。下文的 `python` 可换为新环境解释器。无需GPU。

## 从原始输入到结果

显式输入路径是主入口。当前附件目录为：

```powershell
$attachmentDir = 'D:\MathorCup\2026年第七届MathorCup数学应用挑战赛—大数据竞赛初赛赛题\2026年MathorCup大数据挑战赛-赛道A初赛\附件'
python scripts/run_baseline.py --features "$attachmentDir\1.csv" --targets "$attachmentDir\4.csv" --config configs/exploratory_v0.json
```

若附件位置不同，只改 `$attachmentDir`。程序不会遍历选择同名附件，避免读错版本；上述路径本机存在性与实际运行见 `reports/A_STATUS.md`。

可选 `--run-id my-unique-id`；同名目录存在即失败，不覆盖。`--output-root`仅允许位于本项目 `runs/` 目录内。默认自动生成北京时间时间戳与随机后缀。失败退出码为1，CLI报错；成功退出码为0并输出产物路径。

## 验证 v0 与模型

按字符串 `beer` 字典序排序后，使用固定 `seed=20261024` 的 shuffled 5-fold KFold；不是风格分层。输入行顺序变化不改变划分。保存每个beer的fold及每折风格计数；最小风格3样本，某折可没有该风格。

同一划分比较两个模型：

1. `train_mean`：仅使用训练折各目标的均值。
2. `ridge`：每折重新拟合中位数插补→StandardScaler→Ridge，`alpha=100`、SVD求解器、拟合时线程数限制为1。此alpha是预设的工程探针，未调参或经队员选定。

所有231个特征保留。全数据全缺失列直接报错；某训练折全缺失列保持维数、插补为0，记录该列与所有折内统计。插补、缩放均不在全样本拟合；不做目标再标准化和特征筛选。模型不使用风格。

验证衡量当前采样总体内新beer的表现。未按酿造厂/近重复分组，不能据此证明未见风格、未见酿造厂或外部泛化。已知上游逐品鉴者标准化及汇总，完整原始记录、参数与处理细节仍缺失；不能作全局逆z变换。单次五折没有显著性检验或可靠置信区间。

## 每次运行的文件

独立目录 `runs/<run_id>/`：

| 文件 | 内容 |
|---|---|
| `manifest.json` | running/completed/failed状态、负责人/假设、北京时间、耗时、输入/配置哈希、代码及未提交状态指纹、证据字典哈希、验证/指标版本、环境、指标、产物哈希、局限 |
| `execution_log.jsonl` | 本轮实际执行的输入校验/评估/完成或失败事件与北京时间 |
| `source_snapshot/` | 本轮src/scripts/tests/configs及工程依赖文件副本；原始附件不复制、不修改 |
| `requested_config.json` / `resolved_config.json` | 请求配置原文与实际完整配置 |
| `data_audit.json` | 样本数、字段顺序、缺失、风格数、连接与尺度说明 |
| `folds.csv` / `fold_style_counts.csv` | 固定的beer→fold清单和风格分布；清单哈希见manifest |
| `oof_predictions.csv` | 每模型×beer×目标一行，真值、预测、fold、风格、残差；真实数据共25000行 |
| `target_metrics.csv` | 每模型每目标的pooled OOF MAE、RMSE、R² |
| `fold_target_metrics.csv` | 每模型每折每目标同口径指标 |
| `style_metrics.csv` | 各风格样本数及跨目标误差；仅描述，不推断可靠性 |
| `preprocessing_by_fold.json` | 插补、缩放实际训练统计和训练全缺失列 |
| `summary.json` | 总体指标与局限 |
| `error_traceback.txt` | 仅实际失败且已创建运行目录时写入 |

指标版本为 `standardized-oof-regression-v0`。`macro_target_mae/rmse`为50个目标各自指标的等权均值；`pooled_rmse`为全部样本×目标残差平方均值再开方，二者不可混称。总体R²是可定义目标R²的均值，同时记录数量；恒定目标R²空白/JSON null，不默认为0或1。

无Git提交时 `head=null`。代码文件逐项哈希与快照包含未跟踪文件；不能只凭空的 `git diff` 判断版本相同。运行结束复核原始输入与源码哈希，变化即标failed。运行目录创建前的配置解析、非法ID、重复ID等错误不构成训练运行，也不会生成新manifest。`status=failed`中的部分指标不能作为有效成绩。

## 测试与独立复核

```powershell
python -m pytest -q
```

测试针对显式数据契约、固定划分、训练折插补与均值、全缺失列、OOF覆盖、指标和运行追踪，不用真实标签调参。测试结果与真实实跑编号见状态文件。

另一成员复跑时使用同一输入、配置和对应代码快照，并新建run_id。比较 `folds.csv`哈希、`oof_predictions.csv`数值与指标；运行时间、ID、机器路径和环境信息允许不同。若当前源码已有修改，应在本项目另建复现目录并复制旧 `source_snapshot` 后运行，避免把不同代码的分数归为同一次实验。

## 首轮实际运行与交接

截至 `2026-10-24T17:26:23+08:00`，已完成以下真实运行，均退出码0、manifest为completed；中断发生在运行完成之后，未覆盖或重新运行它们。

| run_id | 开始时间（UTC+8） | 耗时（不含Python进程启动） | 用途 |
|---|---|---:|---|
| A-20261024-001 | 2026-10-24T17:21:40+08:00 | 2.374秒 | 首次基线与固定候选 |
| A-20261024-002 | 2026-10-24T17:21:58+08:00 | 2.010秒 | 相同环境复跑 |

两次使用上面的完整命令，分别追加 `--run-id A-20261024-001` 与 `--run-id A-20261024-002`。下一位复跑者请使用新编号（例如 `C-20261024-001`），不能重用上述ID。

| 模型 | 逐目标MAE均值 | 逐目标RMSE均值 | 逐目标R²均值（50项） | pooled RMSE |
|---|---:|---:|---:|---:|
| train_mean | 0.4175462644 | 0.5691845509 | -0.0088936416 | 0.5795101916 |
| ridge，alpha=100 | 0.4840788846 | 1.6720177555 | -9.7358719308 | 2.0646453472 |

这是附件4已观测标准化尺度的OOF结果，不是原始0–6的误差或官方竞赛成绩。当前固定Ridge在本划分50/50目标RMSE均劣于均值基线，不支持“本固定候选改进基线”的假设；这不构成对全部Ridge方案的否定。保留均值对照和候选的完整失败表现，未继续调参。

误差核查发现：Ridge平方误差的89.3574%集中在beer=156；其 `X2.methyltetrahydrofuran.3.one=12596.43287` 按对应训练折统计缩放后绝对值约1989.6。beer=151的 `X.E..beta.damascenone=5991.012523` 对应约601.5。它们提示当前线性候选对极端输入敏感；尚不能据此判定原始值错误或删样本，也没有进行修改、反变换或截断。来源/测量含义交刘源核验，后续处理须由队员决定且只在训练折拟合。

同环境复现核查已实际完成：两个run的10个核心文件逐字节相同（划分、风格计数、OOF、逐目标/逐折/风格指标、预处理统计、数据审计和两份配置），summary指标完全相等；每个run的24个已登记产物哈希通过。OOF共25000行、每模型×beer×目标恰好一次且全部有限；输入未变，当前源码与运行快照一致。细节在本地 `runs/A-20261024-phase1-audit.json`。此项为A的同环境工程核查，谢小鱼的独立工作副本验收尚未开展，M1整体门槛仍待C复核。

另一个只读AI工程核查已从OOF重算每run的1908个指标值（逐目标、逐折、风格与总体），最大绝对差约 `1.71e-13`；训练折目标均值核对最大差 `6.25e-17`。OOF与原始4.csv真值完全吻合、fold/风格冲突0；指标表分别100/500/44行且键唯一。它核查的是现有产物，没有重新拟合模型，也不代替谢小鱼的独立复跑。

- 运行时Git `HEAD=null`；源码指纹 `f4aabe489d7c25c034154c21541f1b482a9ebed3d24611ca5a71d14fa56b2e7b`。
- `folds.csv` SHA-256：`41847893cdfdf804e723a0fb9eac089678f59a9913f876e1ff51822c99b4407e`。
- 1.csv SHA-256：`419849227a02e0c792cd405e6865035b7f58af1a92efa362dbb68a7ca2882f69`。
- 4.csv SHA-256：`43a7b38682ed81ce64d97ebc1874c09dffac023ade4877f34e3c83ef7d42dc1c`。
- 请求配置SHA-256：`51a334db4a6c2bf7f639509fdc1860326fdfcca48bdabd0d2437640fd8e037fd`。

复现上述字节一致检查（只读已有结果，不训练）：

```powershell
$resultFiles = @('folds.csv','fold_style_counts.csv','oof_predictions.csv','target_metrics.csv','fold_target_metrics.csv','style_metrics.csv','preprocessing_by_fold.json','data_audit.json','requested_config.json','resolved_config.json')
foreach ($name in $resultFiles) {
    $firstHash = (Get-FileHash -Algorithm SHA256 -LiteralPath "runs/A-20261024-001/$name").Hash
    $secondHash = (Get-FileHash -Algorithm SHA256 -LiteralPath "runs/A-20261024-002/$name").Hash
    if ($firstHash -ne $secondHash) { throw "Different output: $name" }
}
```

首轮前最后一次完整测试为49 passed（6.86秒）；code-reviewer复查另实跑49 passed（7.19秒），python-reviewer复查通过。发现并修复的常数小数R²误判和安装入口边界均已回归；这些是AI工程审查，不是三名队员已经确认核心建模。本阶段两次真实训练没有失败run；合成测试中的预期失败不是竞赛实验。恢复中断后未改源码/配置，也未重复无变更的测试。AI过程记录见 `records/ai/A/20261024-baseline-engineering.md`。

## 下一步与决策责任

队员需要决定使用场景/分组验证、主要指标/权重、候选及保留标准；谢小鱼独立复跑并检查，刘源核验异常输入及尺度含义。总控核实原尺度与目标映射、单位、阈值后再升级契约/验证版本。更换口径需要重跑对照，不能与v0直接混比。问题2/3尚未实现，本阶段无官方提交产物。A工程本阶段完成并停止扩大模型工作；未自行提交、推送或操作远端，源码/配置/测试已停止变动，可由总控按分工整合。
