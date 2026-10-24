# 感官评分尺度来源追溯

核查日期：2026-10-24。范围：原论文方法、Zenodo 10653704 的完整补充工作簿和公开处理代码；只读取赛题原始附件，未训练模型，未执行作者代码或加载 pickle。

## 结论

**目前不能有证据地把附件 4.csv 准确逆变换为原始 0–6 分数。** 这不是只差一个全局均值和标准差：原论文说明按品鉴者进行中心化及标准差缩放，然后汇总不同品鉴者的结果；完整的逐品鉴者原始记录、相应转换参数与汇总细节未在本次核查的公开材料中找到。

同时找到两项有用的新证据：

1. 赛题 4.csv 的全部 250 × 50 个感官数值，与原论文工作簿的 `Supplementary File S4` 一致，最大绝对差 `1.1102230246251565e-16`，没有数值差超过 `1e-12`。因此这些目标值沿用了论文公开的标准化数据，而不是本次赛事额外进行了一种未知的目标转换。
2. 完整工作簿有少量独立加料验证试验的原始评分，但它们只有 8 项感官指标，来自另外的验证环节，不能充当 250 款啤酒、50 个指标的完整原始评分或通用逆变换参数。

## 1. 一手来源与下载校验

- 原论文：Schreurs et al., *Predicting and improving complex beer flavor through machine learning*, Nature Communications 15, 2368 (2024)。[期刊原页](https://www.nature.com/articles/s41467-024-46346-0)，[期刊 PDF](https://www.nature.com/articles/s41467-024-46346-0.pdf)。直接打开网页有时遇到重定向；搜索引擎返回了完整方法文本，另有[作者机构 PDF](https://bio.kuleuven.be/eeb/tw/schreurs-etal-natcomm-2024.pdf)。
- 作者数据与代码：[Zenodo 10653704](https://zenodo.org/records/10653704)，页面标示 v3；记录创建于 2024-02-13、最后修改于 2024-03-27。
- 完整工作簿：[Supplemental Files and Figure source files.xlsx](https://zenodo.org/records/10653704/files/Supplemental%20Files%20and%20Figure%20source%20files.xlsx?download=1)。下载文件 5,261,473 字节；本地 MD5 `52645e38d90aafda272532e19e2fea1c` 与 Zenodo 公布值相同。
- 已保存到本报告同级 `source_materials` 目录：完整工作簿、感官 QC Rmd、主图 Rmd、补图 Rmd、建模 Python 文本、README。`workbook-inventory.json` 保存 29 张工作表的名称、可见状态、尺寸及表头。全部工作表可见，未发现隐藏的原始感官数据表。

## 2. 原论文到底标准化了什么

原论文 Methods → Sensory dataset → Trained panel 指出：

> Scores were scaled by standard deviation and mean-centered per taster.

同节说明并非每名品鉴者参加每次品鉴。方法中还说明将不同品鉴者的结果取平均，并在建模部分说明感官属性以 z 分数表示。[原论文方法](https://www.nature.com/articles/s41467-024-46346-0)

**确定的事实**：有逐品鉴者标准化、品鉴者参与不完全一致、结果聚合三个环节。

**尚未确定的细节**：标准化是否严格按“品鉴者 × 属性”分组、均值及标准差基于哪些场次、使用总体还是样本标准差、重复样品/缺失回答怎样加权、导出 S4 之前是否还有额外处理。本次找到的代码从 S4 开始建模，没有展示完整的原始评分到 S4 的预处理过程。

作为数值核验，S4 的 50 列在 250 款啤酒上：

- 列均值范围 `-0.049311815868` 至 `0.062832603384`。
- 样本标准差（ddof=1）范围 `0.369659285591` 至 `0.858463202699`。
- 总体标准差（ddof=0）范围 `0.368919226219` 至 `0.856744555924`。

这支持“它不是以这 250 款的逐列统计量进行一次全局标准化”的判断；不能拿现有 S4 的均值与标准差充当原始 0–6 评分的参数。

## 3. 为什么聚合后的 z 分数不足以准确逆变换

以下为数学说明，不是声称已恢复作者具体算法。对某一属性，假设品鉴者 t 的原始评分为 r，标准化为 `(r - mu_t) / sigma_t`，最终表中保存的是这些标准化值的加权均值。原始评分的加权均值则需要分别恢复每位品鉴者的评分再聚合。

当各品鉴者的 `mu_t`、`sigma_t` 不同且参与集合不固定时，仅知道标准化值的平均数，一般无法推出原始评分的平均数。即使获得一组总体均值、总体标准差，也不能自动解决这个信息丢失问题。要准确恢复，通常需要原始评分表，或足以重建各品鉴者变换和聚合的完整信息。

因此，min–max 到 0–6、乘任意标准差再加 3、正态分位数映射、四舍五入/截断，都只能算另行定义的校准或展示规则，不能表述为“准确恢复真实原始评分”。

## 4. 公开代码提供的证据和缺口

### 感官质量控制脚本

[Sensory data quality control - ANOVA on repeated samples.Rmd](https://zenodo.org/records/10653704/files/Sensory%20data%20quality%20control%20-%20ANOVA%20on%20repeated%20samples.Rmd?download=1) 的本地第 22 行读取 `Raw_Sensory_data_Trained_panel.csv`；第 44 行按 `beer, taster` 分组，第 45 行按 `date` 判断重复品鉴。

这证明作者的分析过程使用过逐品鉴者原始记录。但该 CSV 不在 Zenodo 此版本公开的 12 个文件清单内，也不是完整工作簿的任何一张表。本次针对文件名的公开搜索也未找到可核验的下载位置。因此应表述为“本次核查的公开材料未提供该文件”，不能扩大成“作者从未公开过”。

### 建模代码

[Machine learning models transcript.py](https://zenodo.org/records/10653704/files/Machine%20learning%20models%20transcript.py?download=1) 本地第 73–79 行从 S1、S4 读取特征及标签，`Y` 直接取 `A_malt_all` 至 `overall`。第 87 行拟合的是输入 `scaler_X`；第 88、92–93 行的 `scaler_Y` 相关代码处于注释状态。

因此这里没有可用来逆转原始感官评分的标签 scaler。重新对 S4 拟合一个 scaler，再做 inverse_transform，也只会回到 S4 的现有标准化尺度。

## 5. 完整工作簿中有没有原始 0–6 分数

有部分，但用途不同，不能混用。

| 工作表 | 发现 | 对恢复 S4 的作用 |
|---|---|---|
| Supplementary File S3 | 空白原始评分模板，刻度含 0–6，带选项读取公式 | 解释量表和派生规则；不能提供真实评分 |
| Supplementary File S4 | 250 行 × 50 个标准化感官数值，另有 3 个元数据字段 | 与本地 4.csv 全量一致 |
| Sensory names | 50 个专家指标的命名、类型、分类 | 没有标准化所需的均值/标准差 |
| Supplementary Table S2 | 50 个属性 × 12 个重复啤酒的 ANOVA p 值 | 是检验结果，不是原始分数 |
| Validation Results 1 | 42 行，8 个感官评分字段，观测值范围 0–6 | 独立加料验证试验 |
| Validation Results 2 | 26 行，同样 8 个评分字段，观测值范围 0–5 | 独立加料验证试验；0–5 是观测范围，不能据此认定量表只有 6 档 |
| Validation Results 3 | 26 行，同样 8 个评分字段，观测值范围 0–6 | 独立加料验证试验 |
| Validation Details / Concentrations | 匿名样品代码、基酒、加料/对照状态及配方条件 | 有助复现验证试验，不能提供全部原始训练评分 |

这 8 个验证指标是 Malt、Sweetness、Hops、Bitterness、Esters、Fullness (body)、Alcohol (warming)、Overall appreciation。

[Main Figure Generator.Rmd](https://zenodo.org/records/10653704/files/Main%20Figure%20Generator.Rmd?download=1) 本地第 718–758 行读取上述验证表，并按日期与匿名样品代码连接 `Validation Details`，将分数整理为 Spiked / Control 的配对结果。后续比较加料与对照的差异和偏好比例。

**不能直接把 Validation Results 的 Beer 数字当成 S4 的 beer 键。** 例如 2020-07-13 的样品代码 506 和 913 都对应 `BaseBeer=63`，分别是加料样品和对照；匿名样品代码还必须结合日期解释。不同实验的原始评分不应直接拼接为 S4 的缺失标签。

## 6. 另一个量表细节：24 项子风味不是独立滑杆

`Sensory names` 将专家面板的 50 项标为 26 个 `numeric`、24 个 `categorical`。需要结合评分卡公式理解，不能将 categorical 直接当成现成的 0/1 目标。

在 `Supplementary File S3` 中：

- `Q7` 从麦芽总体强度的 0–6 刻度读取值。
- `Q10 = IF(ISBLANK(C10),0,Q7)`：若没有勾选谷物子风味，该项为 0；若勾选，继承总体麦芽强度。
- `Q12`、`Q14`、`Q16` 对面包、焦糖、烟熏子风味使用相同逻辑。
- `Q23 = IF(ISBLANK(C23),0,Q20)`：柑橘子风味继承酒花总体强度。
- `Q36 = IF(ISBLANK(C36),0,Q33)`：乙酸乙酯/指甲油子风味继承酯总体强度。
- 味觉侧 `AG` 列有对应结构。

因此，至少在所提供的原始模板中，这 24 项先经“是否勾选 × 对应总体强度”形成派生值。它们并非 24 个独立的 0–6 强度提问，也不能只凭类型字段就把 S4 的相关列直接作为二分类标签。作者是否对所有实验场次完全使用同一模板，仍须原始数据/预处理代码确认。

## 7. 建议交给总控的下一步

1. 将“准确恢复原始 0–6 分数”标为数据缺口，不伪造逆变换。
2. 建模与评估先明确使用 S4 的已有标准化尺度；如赛事确实要求输出 0–6，则把输出校准独立为可替换模块，等待官方澄清或补充真实校准资料。
3. 如准备向组委会提问，问题应具体到：是否允许直接预测附件 4 的标准化分数；若必须 0–6，是否提供原始逐品鉴者评分、转换/汇总代码，或者指定统一映射。本文仅准备问题，未向外发送。
4. 若需要向原作者求证，最有价值的是请求 `Raw_Sensory_data_Trained_panel.csv` 及“原始评分 → Supplemental File S4”的完整预处理脚本，而不是只索取 50 个总体均值与标准差。本文未联系作者。
5. 原作者既有模型、加料验证数据和效果只作为来源证据；是否允许作为比赛补充数据，以及怎样引用，仍服从比赛规则。此次未把它们用于训练。

本次到此结束来源追溯：已有足够证据说明简单逆 z 转换不成立，且明确了真正缺失的材料。没有为填补空缺而推断一套不存在的转换参数。
