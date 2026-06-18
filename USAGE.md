# fiction-distiller 使用教程

## 快速开始

### 1. 提供原文

在对话中粘贴一篇短篇小说原文（建议 3000-20000 字）。系统会自动：

- 识别篇幅
- 选择对应知识路径
- 执行完整七步 pipeline

### 2. 查看输出

所有生成内容保存在 `output/` 目录下：

| 输出文件 | 内容 |
|----------|------|
| `《原文》.analysis.json` | 原文字数分析 |
| `《原文》.skeleton.yaml` | 五维骨架卡 |
| `《原文》_分章.variables.json` | 换元清单 |
| `《新篇名》.txt` | 新短篇小说正文 |
| `《新篇名》.originality.json` | 原创性验证报告 |
| `《新篇名》.anti_detection.json` | 反检测验证报告 |
| `《新篇名》.deviation.json` | 字数偏差报告 |
| `《新篇名》.quality.json` + `.quality.html` | 统一质量报告 |

### 3. 检查质量

核心指标参考：

| 指标 | 通过标准 |
|------|----------|
| 总字数偏差 | ±5% |
| 5-gram 重合率 | < 5% |
| 8-gram 重合数 | < 10 |
| 真实变量残留 | 0 |
| 最长公共子串 | < 8 字 |
| 突发性 Burstiness | > 0.7 |
| 硬黑名单 AI 特征词 | 0 |
| 软黑名单 AI 特征词 | ≤ 5 |

## 工具单独使用

所有工具位于 `tools/` 目录，可独立运行。

### word_count_analyzer.py — 字数分析

```bash
python tools/word_count_analyzer.py 原文.txt [输出.json]
```

输出原文总字数、段落数、句长分布、对话占比、叙述/描写比例，并生成字数预算表。

### skeleton_extractor.py — 骨架提取

```bash
python tools/skeleton_extractor.py 原文.txt [输出.yaml]
```

提取五维骨架：结构、节奏、视角、语言、情绪。

### variable_annotator.py — 变量标注

```bash
python tools/variable_annotator.py 原文.txt [输出.json]
```

扫描六类关节点：人物、地点、事件、道具、台词、关系。

### originality_checker.py — 原创性验证

```bash
python tools/originality_checker.py 原文.txt 新篇.txt [换元清单.json] [禁忌清单.json] [输出.json]
```

检查项：
- 3/5/8/12-gram 重合率
- 最长公共子串（含位置定位）
- 三级残留检测（真实残留 / 7字+潜在残留 / 4-6字日常短语）
- 段落级原创性分析
- 同义替换禁忌扫描
- 句子结构相似度

### anti_detection_checker.py — 反检测验证

```bash
python tools/anti_detection_checker.py 新篇.txt [输出.json]
```

检查项：
- 突发性 Burstiness（全局 + 段落级）
- 短句占比（目标 ≥15%）
- 长短句交替率（目标 ≥10%）
- 硬黑名单 AI 特征词（目标 0）
- 软黑名单 AI 特征词（目标 ≤5）
- 硬模式化标记（目标 0）
- 软模式化标记（目标 ≤3）

### word_count_adjuster.py — 字数对齐

```bash
python tools/word_count_adjuster.py 新篇.txt 字数预算.json [输出.json]
```

逐段对比实际字数与预算，输出偏差和建议。

### quality_report.py — 统一质量报告

```bash
python tools/quality_report.py 原文.txt 新篇.txt [换元清单.json] [禁忌清单.json]
```

集成字数、原创性、反检测三维度，输出：
- `新篇名.quality.json` — 完整 JSON 报告
- `新篇名.quality.html` — 可视化 HTML 报告

## 分步工作流（手动模式）

如果需要手动控制每一步：

### Step 1: 字数分析

```bash
python tools/word_count_analyzer.py 原文.txt output/原文.analysis.json
```

### Step 2: 骨架提取

参考 `prompts/p01-skeleton-extract.md`，将原文和字数分析结果提供给 AI。

### Step 3: 变量标注

参考 `prompts/p02-variable-annotate.md`，将原文和骨架卡提供给 AI。
输出换元清单（含影响层级和同义替换禁忌）。

### Step 4: 新变量设计

参考 `prompts/p03-new-variable-design.md`，将骨架卡和换元清单提供给 AI。
输出新变量方案（含禁忌清单）。

### Step 5: 逐段生成

参考 `prompts/p04-paragraph-generate.md`，逐段生成新短篇。
**关键**：这是"功能等价重写"模式，不是逐句改写原文。

### Step 6: 字数对齐

```bash
python tools/word_count_adjuster.py 新篇.txt output/原文.analysis.json
```

参考 `prompts/p06-word-count-fix.md` 进行修正。

### Step 7: 反检测 & 原创性验证

```bash
# 原创性检查
python tools/originality_checker.py 原文.txt 新篇.txt output/换元清单.json

# 反检测检查
python tools/anti_detection_checker.py 新篇.txt

# 统一质量报告
python tools/quality_report.py 原文.txt 新篇.txt output/换元清单.json
```

### Step 8: 人味化润色（如需要）

参考 `prompts/p05-humanize.md`，对未通过反检测的段落进行人味化处理。

### Step 9: 自检查（如需要）

参考 `prompts/p07-self-check.md`，进行最终自检。

## 常见问题

### Q: 5-gram 重合率超标怎么办？

1. 运行 `quality_report.py` 查看高风险段落
2. 重点重写与原文重叠最高的段落
3. 使用"功能等价重写"模式：只看骨架功能，不看原文内容
4. 对照同义替换禁忌清单，确保未使用原文表达

### Q: 字数偏差超标怎么办？

1. 运行 `word_count_adjuster.py` 查看逐段偏差
2. 偏短段落：增加感官细节、心理活动、对话反应
3. 偏长段落：删除冗余修饰、合并简单句、压缩对话提示
4. 修正时必须保持原创性，不得引入原文片段

### Q: 突发性 Burstiness 不足怎么办？

1. 增加长短句交错：每段至少 1 个短句（≤10字）和 1 个长句（≥25字）
2. 在紧张处插入极短句（2-5字）
3. 删除连续 3 句以上长度相近的句子
4. 增加口语化表达

### Q: AI 特征词被检测到怎么办？

1. 硬黑名单词（综上所述、深刻地揭示了等）：必须删除
2. 软黑名单词（首先、其次等）：全文 ≤5 次可保留
3. 将书面化表达改为口语化表达
4. 查看 `quality_report.html` 中每个命中的上下文

### Q: 生成的新篇仍然是"换名微调"怎么办？

这说明 p04 生成模式不对。请确保：
1. 不要看原文具体内容，只看骨架卡的功能描述
2. 从空白开始写作，不要逐句对照原文
3. 使用"功能等价重写"原则：骨架功能相同，表达完全不同
4. 参考核心修复说明中的正确/错误示例

## 文件依赖关系

```
原文.txt
  → word_count_analyzer.py → analysis.json
  → skeleton_extractor.py → skeleton.yaml
  → variable_annotator.py → variables.json
  → new_variable_designer.py → new_variables.json

新篇.txt
  → originality_checker.py (原文 + 新篇 + variables.json) → originality.json
  → anti_detection_checker.py (新篇) → anti_detection.json
  → word_count_adjuster.py (新篇 + analysis.json) → deviation.json
  → quality_report.py (原文 + 新篇 + variables.json) → quality.json + quality.html
```