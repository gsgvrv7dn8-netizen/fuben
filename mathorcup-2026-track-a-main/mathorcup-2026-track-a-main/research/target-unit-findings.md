# 目标字典与化学单位/变换核验

核查日期：2026-10-24。只读原始附件；未训练模型。

## 主要结论

- 4.csv 的 50 个感官目标均与 8.xlsx 的 Trained panel 元数据逐项对应；3.xlsx summary 通过三个显式拼写/大小写别名可覆盖这 50 项。
- 评分卡还含 Aroma/Flavour 的两个 Acetaldehyde 项（Q45、AG45），4.csv 没有对应感官标签。化学 acetaldehyde 浓度不能代替它们。
- summary 的 barnyard 在全部 12 张卡都错误引用 AG76（Stale hops），语义正确位置是 AG90（Barnyard/horsey）。本次只记录，没有修改原表。
- AG62 和 AG94 有公式，但前者无感官项目名称，后者邻接 Comments。公式存在并不构成额外有标签目标。
- 原始感官 0–6 尺度和官方输出范围仍未解决；此字典用于对齐，不是自行宣布官方要求。

## 目标的层次与计数

Aroma 与 Flavour 的 Malt/Hops/Esters 各有一个总强度及四个子描述词，共 2×3×5=30 个 A_/F_ 标签。24 个子描述词公式不是独立选 0–6，而是 IF(未勾选,0,对应总强度)，元数据也标为 categorical；这是原评分卡编码结构，不能把标准化后的值直接认作分类等级。
另有 7 个一般感官项（body、alcohol、bitternes、sweetness、co2、acidity、aftertaste）、6 个缺陷项、6 个风格附加项和 overall，共 20 项，合计 50。卡面额外的两个 Acetaldehyde 项使有名称的感官评分位置达到 52。元数据按 Category_Paper 归为 Aroma 15、Taste 30、Palate 4、Overall 1，与卡面左右排版不是同一分类。
题面“约 40”没有与这几个集合精确对应。30 个 A_/F_ 加 7 个一般项为 37，再加未入标签的两个 Acetaldehyde 为 39，只是可能解释近似数量的算术组合，并非官方意图证据。必须查官方说明后再决定输出范围，不能自行删减至 40。

## 化学映射与变换覆盖

- 231 个 1.csv 特征全部通过 field_name_R 找到阈值元数据；2.csv 的231个显示名称按现有顺序重算 Spearman 的全矩阵最大误差为 6.6613381477509392e-16。这证实当前附件顺序对应，但字典仍保存两套名字。
- 70/231 个特征在校准化学表中有同名列；75/231 个特征有非空来源单位。
- 严格逐值核验：37 列为 log10（仅正值有效配对），1 列为 identity，0 列为 ln，193 列仍为 unknown。
- unknown 中 32 列虽有校准对照、且多数点接近 identity，但存在实质差异；其余列缺少校准对照，不能仅凭正负号或范围判断。CSV 保留每列失败 beer 编号和差异样例。
- 43/231 个特征在来源表至少有一个数值阈值；有阈值不等于已可无条件做缺陷约束。

比较容差取 1.csv 原始文本末位精度的半个单位（包括科学计数法）加浮点运算噪声 1e-12×max(1,|对照|)，避免把 8.95e-05 与 8.94815e-05 这种显示舍入误判为数据变换。只有一个候选变换在其适用域的所有有效配对都通过、且至少三个配对时才标 confirmed。这里的确证限于该有限数据及有效域，不证明未观测数据上的处理机制。

37 个 log10 列包含 pH、ethanol、bitterness、color、CO2 等。非正校准值对应 1.csv 有限数值，说明存在替换/预处理；不能把这些值逆变换后当真实实测浓度，也不能把它们自动叫检测下限。校准表本身还存在负值及缺失，因此也不是无需核验的绝对真值。

## 五项重点缺陷

| 项目 | 化学列 / 感官列 | 来源单位与阈值 | 当前可用性 |
|---|---|---|---|
| DMS | DMS / dms | ug/L；均值17.25，中位19 | 249个正值配对为log10；beer=10校准值为0但输入有限，须处理替换语义；阈值均值/中位尚未选择 |
| 4VG | X4VG / X4vg | mg/L；均值0.206333333，中位0.2 | 82个正值配对为log10；168个校准零值对应固定替换值，不能当168个实测正浓度 |
| Diacetyl | X2.3.butanedione / diacetyl | mg/L；均值0.29925，中位0.09 | 238/241个有效配对符合identity，但beer 151、156、34明显不同；全列变换仍unknown，需处理差异及9个输入缺失 |
| trans-2-nonenal | X.E..2.nonenal / t2n | mg/L；两种阈值均缺失 | 247/249个配对符合identity，beer158、130不同；阈值和全列尺度未闭合 |
| Stale hops | 未找到单独同名化学测量列 / stale_hops | 缺少单一物质与单位阈值 | 是现有感官目标；aroma_hops_sum为总酒花香气汇总，不能自动充当其化学代理 |

阈值 mean 和 median 是来源数据的两个汇总版本，不是可任选后隐瞒选择的同一常数；尤其 Diacetyl 两值差异较大。目标缺陷感官分数与相应化学浓度是不同变量，不能用标准化 dms/diacetyl 分数直接比较 ug/L 或 mg/L 阈值。

## 尚不能识别的部分

- 未从本地附件取得明确检测下限/定量下限或零值替换规范；来源字段中 NA/空值保留 unknown，不填文献常识值。
- 无校准对照列的单位即使给出，也不足以证明 1.csv 的存储尺度；单位与变换分别记录。
- 8.xlsx 部分显示名存在字符编码问题，以及字段名与显示化学名不完全相符的条目；保留原文，不能用模糊名称匹配悄悄改名。
- 32列多数identity而少数不一致可能源于处理差异、数据修订或其他原因；本核查不猜测原因，也不自动以校准表覆盖比赛输入。

## 复现与文件

运行：`python research/audit_units_targets.py --source D:\MathorCup`。需要 pandas、numpy、openpyxl。脚本只写同目录的 target-dictionary.csv、chemical-units.csv、target-unit-findings.md；原始附件保持只读。

- target-dictionary.csv：50个有标签目标、2个卡片额外感官项、2个无标签公式位置、1个自由文本位置，共55行；官方输出范围均标 unresolved。
- chemical-units.csv：231行，记录来源字段/单位、每种变换对比、失败样本、阈值及条件可用性。

来源 SHA-256：

- `1.csv`：`419849227a02e0c792cd405e6865035b7f58af1a92efa362dbb68a7ca2882f69`；`D:\MathorCup\2026年第七届MathorCup数学应用挑战赛—大数据竞赛初赛赛题\2026年MathorCup大数据挑战赛-赛道A初赛\附件\1.csv`
- `2.csv`：`415709ac10f2f730d31f249bd6ac108250bdfbfd62e0055f4d8db9b41ec9cc4c`；`D:\MathorCup\2026年第七届MathorCup数学应用挑战赛—大数据竞赛初赛赛题\2026年MathorCup大数据挑战赛-赛道A初赛\附件\2.csv`
- `3.xlsx`：`fe4dcabd48431e6d677c095962ea9c447e10e509c4f3f8dd511a48c5541ab587`；`D:\MathorCup\2026年第七届MathorCup数学应用挑战赛—大数据竞赛初赛赛题\2026年MathorCup大数据挑战赛-赛道A初赛\附件\3.xlsx`
- `4.csv`：`43a7b38682ed81ce64d97ebc1874c09dffac023ade4877f34e3c83ef7d42dc1c`；`D:\MathorCup\2026年第七届MathorCup数学应用挑战赛—大数据竞赛初赛赛题\2026年MathorCup大数据挑战赛-赛道A初赛\附件\4.csv`
- `8.xlsx`：`f2316766792111d98281bd35c8403682be8c8069d166a7a7d5887ffbb227700a`；`D:\MathorCup\2026年第七届MathorCup数学应用挑战赛—大数据竞赛初赛赛题\2026年MathorCup大数据挑战赛-赛道A初赛\附件\8.xlsx`
