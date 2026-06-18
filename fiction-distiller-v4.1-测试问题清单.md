# fiction-distiller v4.1 端到端测试问题清单

> 测试对象：短篇换元仿写技能库 v4.1  
> 测试文本：《被妈妈关进杂物间7天后》（约8099字网文短篇）  
> 测试日期：2026-06-18  
> 状态：全部通过 ✅ 七步流程已执行完毕

---

## 最初发现的问题

| 编号 | 严重程度 | 问题 | 状态 |
|------|----------|------|------|
| P1 | 高 | word_count_analyzer 按回车分段落，网文单句段导致341段预算表不可用 | ✅ 已修复 |
| P2 | 中 | 原文文件编码为 GB18030，工具链全部假设 UTF-8 导致崩溃 | ✅ 已修复 |
| P3 | 中 | analysis.json 段落数341，预算表同样341条，超出实际阅读段落 | ✅ 已修复 |
| P4 | 低 | 描写/叙述比例估算基于"的得地"和感官词计数，过于粗糙 | 🔵 已知（非bug） |
| P5 | 低 | quality_report.py 曾依赖外部 checker module 导入，路径可能不对 | ✅ 无需修复（自包含） |

## 迭代中发现的额外问题

| 编号 | 严重程度 | 问题 | 状态 |
|------|----------|------|------|
| P6 | 中 | "又""既"在 AI_WORDS_SOFT_CN 软黑名单中，导致日常用词误报 | ✅ 已修复 |
| P7 | 中 | "最后"在 AI_WORDS_SOFT_CN 软黑名单中，出现9次日常使用全部误报 | ✅ 已修复 |
| P8 | 中 | 硬模式正则 `第一.*第二.*第三` 误报"第一名"等日常短语 | ✅ 已修复 |
| P9 | 低 | quality_report.py 在 Windows GBK 控制台打印 emoji 触发 UnicodeEncodeError | ✅ 已修复 |
| P10 | 高 | word_count_adjuster.analyze_deviation 用 `\n+` 分段 + 索引匹配预算，新篇章节目录结构不同导致总字数仅算到首8段（386/8099） | ✅ 已修复 |

## 修复详情

### P1 / P3 — 网文段落智能合并

- **问题**：`word_count_analyzer.py` 按 `split('\n+')` 分段，网文每行一句导致8099字分341段，预算表每段只有20-50字
- **修复**：增加逻辑段落合并，连续非空行合并，最小段落阈值80中文字，341→8段
- **文件**：`word_count_analyzer.py`

### P2 — 文件编码自动检测

- **问题**：所有工具使用 `open(path, encoding='utf-8')`，输入文件如果是 GB18030/GBK 编码则直接崩溃
- **修复**：创建 `encoding_utils.py` 共享模块，提供 `read_text_safe()` 函数：先试 UTF-8 → 失败则用 chardet 检测 → GBK/GB2312 转为 GB18030 解码。更新6个工具的读取入口
- **文件**：`encoding_utils.py`（新建）, `word_count_analyzer.py`, `skeleton_extractor.py`, `variable_annotator.py`, `originality_checker.py`, `quality_report.py`

### P5 — quality_report.py 模块依赖

- 经查 `quality_report.py` 完全不 import 其他 checker 模块，是自包含实现 → 无需修复

### P6 / P7 — 软黑名单日常词误报

- **问题**：`AI_WORDS_SOFT_CN` 包含"又""既""最后"等中文日常高频词，导致正常行文被标记为 AI 特征
- **修复**：从软黑名单中移除 `'又'`, `'既'`, `'最后'`
- **文件**：`anti_detection_checker.py`
- **建议**：软黑名单应定期审查，仅保留真正的 AI 写作特征词

### P8 — 硬模式正则误报

- **问题**：`第一.*第二.*第三` 正则匹配到"第一名同学考了...第二名同学考了...第三名同学考了"等日常表述
- **修复**：改为行首匹配 `^第一、...^第二、...^第三、`
- **文件**：`anti_detection_checker.py`

### P9 — GBK 控制台 emoji 崩溃

- **问题**：`print(f"✅ {key}: {value}")` 在 Windows GBK 控制台触发 `UnicodeEncodeError`
- **修复**：将控制台输出 emoji 替换为 ASCII 符号 `[PASS]` `[WARN]` `[FAIL]`；HTML/JSON 输出保持 emoji 不变
- **文件**：`quality_report.py`

### P10 — quality_report 字数统计错误（新篇章节目录匹配偏差）

- **问题**：`word_count_adjuster.analyze_deviation()` 用 `\n+` 分段原文，再按索引匹配预算段落。新篇使用章节目录（`# 第X章`）+ 双空行分段，段落数 8→233，索引匹配只找到前8段（386字），其余7917字全部丢失。`quality_report.py` 依赖此函数的 `total_actual`，导致显示 **386/8099（-95.23%）**
- **根因**：
  1. `split_paragraphs()` 在 `word_count_adjuster.py` 和 `word_count_analyzer.py` 中不同步——前者用 `\n+`，后者已改为智能合并
  2. 总字数计算依赖段落索引匹配的求和，而非全文字数统计
- **修复**：
  1. `analyze_deviation()` 总字数改为 `count_chinese_chars(new_text)` 直接统计，不依赖段落匹配
  2. `split_paragraphs()` 在 `word_count_adjuster.py` 中改为智能合并（与 `word_count_analyzer.py` 一致）
  3. 增加 `misaligned` 标记，段落数不匹配时 quality_report HTML 省略段落级对比表
- **教训**：字数统计必须独立于段落结构分析计算，段落级对比不能污染总数

## 验证结果

v4.1 端到端测试在《被妈妈关进杂物间7天后》上运行完整七步流程后，**所有指标通过**：

| 检查项 | 结果 | 目标 | 实测 |
|--------|------|------|------|
| 字数偏差 | ✅ | ±5% | +2.5% |
| 5-gram 重合率 | ✅ | <5% | 0.11% |
| 8-gram 重合数 | ✅ | <10 | 0 |
| 最长公共子串 | ✅ | <8字 | 6字 |
| 真实变量残留 | ✅ | 0 | 0 |
| 句子结构相似度 | ✅ | <50% | 5.61% |
| 突发性 Burstiness | ✅ | >0.7 | 0.709 |
| 短句占比 | ✅ | ≥15% | 41.9% |
| 长短句交替率 | ✅ | ≥10% | 50.5% |
| 硬AI特征词 | ✅ | 0 | 0 |
| 软AI特征词 | ✅ | ≤5 | 1 |
| 硬模式化标记 | ✅ | 0 | 0 |
| 软模式化标记 | ✅ | ≤3 | 0 |

## 仍然存在的注意事项

1. **段落合并阈值需要针对文本类型调整**：80 字对网文有效，但诗歌/剧本/对话密集短篇可能需要更小阈值
2. **软黑名单维护**：建议每两次迭代审查一次 `AI_WORDS_SOFT_CN`，移除被误伤的日常用词
3. **python 运行路径**：`encoding_utils.py` 通过同目录相对 import 工作，需确保 `python tool.py` 在 tools 目录或 project root 执行

---

*本清单在测试过程中持续更新。*
