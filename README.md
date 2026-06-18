# fiction-distiller

> 短篇换元仿写器——自诸说部文字中提取叙事骨架，将人物/情节/设定/台词全部替换为原创内容，生成字数相近、风格神似、内容全新、可反检测的短篇小说。

## 这是什么

一个支持 **opencode**、**Claude Code** 和 **WorkBuddy** 三平台的短篇换元仿写技能。核心能力：**你给一篇短篇小说，它提取叙事骨架，将所有内容变量替换为原创内容，输出一篇字数相近、风格神似、内容全新、能规避 AI 检测的新短篇小说。**

不是改写情节，不是替换人物名——只借鉴叙事骨架（结构、节奏、视角、语言、情绪），把人物、情节、设定、台词全部替换为全新原创内容。

**版本**: v4.1 (2026-06-18)

## v4.1 核心修复

v4.0 端到端测试发现三大核心问题，v4.1 全部修复：

| 问题 | 根因 | 修复 |
|------|------|------|
| 5-gram重合22%、句式一一对应 | 生成prompt本质是"换名微调" | 重写 p04 为"功能等价重写"模式，增加4字禁止硬约束 |
| 工具误报（4-6字日常短语、AI特征词） | 阈值过严、分类过粗 | originality_checker 三级残留检测；anti_detection_checker 硬/软黑名单分级 |
| 字数/原创性/反检测三个维度未联动 | 生成prompt无原创性约束 | p04/p05/p06 嵌入约束；新增 quality_report.py 统一报告 |

## v4.0 新增功能

- ✅ **短篇换元仿写**：从短篇提取叙事骨架，替换全部变量，生成等字数新短篇
- ✅ **七步工作流**：字数分析 → 骨架提取 → 变量标注 → 新变量设计 → 逐段生成 → 字数对齐 → 反检测验证
- ✅ **反检测技术栈**：困惑度/突发性检测、长短句交错、人味化注入、AI特征词分级黑名单
- ✅ **字数对齐系统**：段落级字数预算 ±5%，扩写/压缩技巧
- ✅ **原创性三关验证**：N-gram重合、变量残留、LCS检测
- ✅ **7个分离式Prompt**：p01-p07，每步一个任务
- ✅ **10个Python工具**：分析、提取、标注、验证、报告
- ✅ **4个新知识模块**：short-substitution/、anti-detection-short/、word-count-control/、originality-check/
- ✅ **三平台同步**：opencode/claude/workbuddy 完整独立副本

## 架构

三层懒加载知识库 + 七步工作流：

```
🔴 基础层（始终加载）
├── general-style/           文体学 · 叙事学 · 修辞学 · 计量学 · 成像理论
├── author-fingerprint/      词汇 · 句式 · 修辞 · 叙事声音 · 标点 · 跨作品指纹
├── short-substitution/      换元仿写核心方法 · 骨架提取 · 变量标注 · 四层换元 · 字数预算 · 七步流程
├── anti-detection-short/    检测原理 · 人味化 · 节奏扰动 · AI特征词黑名单 · 验证流程
├── word-count-control/      字数分析 · 预算表 · 扩写压缩
└── originality-check/        N-gram检测 · 变量残留 · 人工复核

🟡 体裁层（按文本类型加载）
├── long-fiction/            长篇：冲突 · 叙述 · 结构 · 文体 · 修改
├── short-fiction/           短篇：唯一效果 · 战略选择 · 细节 · 结构 · 美学
└── net-style/               网文：流派 · 爽点 · 世界观 · 人设 · 节奏 · 情感

🟢 方法层（创作阶段加载）
└── ai-distillation/         特征提取 · 指纹验证 · 模仿策略 · 原创性评估
```

共 49 个知识文件，5 个模块 v4.0 新增。

## 七步工作流

```
输入原文短篇
    ↓
[Step 1] 字数/结构分析    → word_count_analyzer.py → 字数预算表
    ↓
[Step 2] 五维骨架提取      → skeleton_extractor.py → 骨架卡
    ↓
[Step 3] 关节点/变量标注   → variable_annotator.py → 换元清单
    ↓
[Step 4] 原创内容设计      → new_variable_designer.py → 新变量方案
    ↓
[Step 5] 按骨架逐段生成    → short_generator.py → 新短篇初稿
    ↓
[Step 6] 字数对齐修正      → word_count_adjuster.py → 修正稿
    ↓
[Step 7] 反检测 & 原创性   → originality_checker.py + anti_detection_checker.py → 验证报告
    ↓
质量总报告                 → quality_report.py → HTML + JSON 报告
```

## 工具链

| 工具 | 功能 |
|------|------|
| `word_count_analyzer.py` | 分析原文字数结构，生成字数预算表 |
| `skeleton_extractor.py` | 提取五维骨架（结构、节奏、视角、语言、情绪） |
| `variable_annotator.py` | 标注关节点/变量，生成换元清单 |
| `new_variable_designer.py` | 设计全新变量方案 |
| `short_generator.py` | 调用 LLM 按骨架逐段生成 |
| `word_count_adjuster.py` | 段落级字数对齐修正 |
| `originality_checker.py` | 原创性验证（N-gram/LCS/残留/段落级） |
| `anti_detection_checker.py` | 反检测验证（突发性/AI词/模式标记/节奏） |
| `quality_report.py` | 统一质量报告（字数+原创性+反检测） |
| `make_curated_vars.py` | 辅助：精编变量清单 |

## Prompt 文件

| 文件 | 用途 |
|------|------|
| `p01-skeleton-extract.md` | 提取五维骨架 |
| `p02-variable-annotate.md` | 标注关节点变量（含影响层级+同义禁忌+危险片段） |
| `p03-new-variable-design.md` | 设计新变量方案（含零残留+反检测约束） |
| `p04-paragraph-generate.md` | 按骨架逐段生成（**功能等价重写模式**） |
| `p05-humanize.md` | 人味化润色（含分级黑名单+原文危险片段扫描） |
| `p06-word-count-fix.md` | 字数对齐修正（含原创性约束） |
| `p07-self-check.md` | 自检查与反检测（含同义禁忌扫描+句式残留检测） |

## 关键指标

| 指标 | 目标 |
|------|------|
| 字数相似度 | ±5% |
| 5-gram 重合率 | < 5% |
| 8-gram 重合数 | < 10 |
| 变量残留（真实） | 0 |
| 最长公共子串 | < 8 字 |
| 句子结构相似度 | < 0.5 |
| 突发性 Burstiness | > 0.7 |
| 短句占比 | ≥ 15% |
| AI 特征词（硬黑名单） | 0 |
| AI 特征词（软黑名单） | ≤ 5 |

## 红线

```
❌ 跳过知识索引
❌ 复制原文任何连续句子（≥4字）
❌ 沿用原文情节/场景/对白/专名
❌ 逐句对应原文改写（换名微调）
❌ 使用同义替换禁忌清单中的词
❌ 长篇以整体印象代替逐章分析
❌ 修改或覆盖 output/ 外的任何项目文件
```

## 使用方式

### 快速开始

在对话中提供短篇小说文本即可。系统自动判断篇幅、选择知识路径、执行蒸馏到创作的完整 pipeline。

### 各平台安装

| 平台 | 安装方式 |
|------|----------|
| OpenCode | 将 `.opencode/skills/fiction-distiller/` 复制到技能目录 |
| Claude Code | 将 `.claude/skills/fiction-distiller/` 复制到项目 `.claude/skills/` 目录 |
| WorkBuddy | 将 `.workbuddy/skills/fiction-distiller/` 复制到项目 `.workbuddy/skills/` 目录 |

### 用法示例

```
用户：仿写这篇短篇小说 [粘贴原文]

AI 自动执行：
1. 确认字数目标（±5%）
2. Step 1-7 全流程
3. 输出：骨架卡 + 换元清单 + 新短篇 + 验证报告
```

### 工具单独使用

```bash
# 字数分析
python word_count_analyzer.py 原文.txt 分析结果.json

# 原创性检查（支持4字以上残留检测、段落级分析）
python originality_checker.py 原文.txt 新篇.txt [换元清单.json] [禁忌清单.json]

# 反检测检查（硬/软黑名单分级、节奏指标）
python anti_detection_checker.py 新篇.txt

# 统一质量报告（集成三维度）
python quality_report.py 原文.txt 新篇.txt [换元清单.json] [禁忌清单.json]

# 字数对齐修正
python word_count_adjuster.py 新篇.txt 字数预算.json
```

## 项目结构

```
.opencode/skills/fiction-distiller/
├── SKILL.md                    ← 技能入口（v4.1）
├── knowledge/                  ← 知识库（49 个主题文件）
│   ├── index.md
│   ├── general-style/          ← 风格分析（5文件）
│   ├── author-fingerprint/     ← 作者指纹（6文件）
│   ├── short-substitution/     ← 换元仿写（6文件）v4.0新增
│   ├── anti-detection-short/   ← 反检测（5文件）v4.0新增
│   ├── word-count-control/     ← 字数控制（3文件）v4.0新增
│   ├── originality-check/      ← 原创性验证（3文件）v4.0新增
│   ├── long-fiction/           ← 长篇（5文件）
│   ├── short-fiction/          ← 短篇（5文件）
│   ├── net-style/              ← 网文（7文件）
│   └── ai-distillation/        ← 方法论（4文件）
├── prompts/                    ← 7步分离式Prompt v4.1
│   ├── p01-skeleton-extract.md
│   ├── p02-variable-annotate.md  ← 含影响层级+同义禁忌+危险片段
│   ├── p03-new-variable-design.md ← 含4字禁止+反检测约束
│   ├── p04-paragraph-generate.md  ← 功能等价重写模式
│   ├── p05-humanize.md            ← 含分级黑名单+危险片段扫描
│   ├── p06-word-count-fix.md      ← 含原创性约束
│   └── p07-self-check.md          ← 含同义禁忌扫描+句式残留检测
├── tools/                       ← 10个Python工具
│   ├── word_count_analyzer.py
│   ├── skeleton_extractor.py
│   ├── variable_annotator.py
│   ├── new_variable_designer.py
│   ├── short_generator.py
│   ├── word_count_adjuster.py
│   ├── originality_checker.py    ← v4.1 三级残留+段落级分析
│   ├── anti_detection_checker.py ← v4.1 硬/软黑名单+节奏指标
│   ├── quality_report.py         ← v4.1新增 统一质量报告
│   └── make_curated_vars.py
└── output/                       ← 生成内容输出目录

.claude/skills/fiction-distiller/     ← Claude Code 完整副本
.workbuddy/skills/fiction-distiller/  ← WorkBuddy 完整副本

templates/                ← 输出模板
├── style-model-card.md
├── short-skeleton-card.md  ← v4.0新增 骨架卡模板
├── variable-list.md         ← v4.0新增 换元清单模板
├── verification-report.md    ← v4.0新增 验证报告模板
├── outline.md
├── originality-statement.md
├── short-story.md
└── long-story-chapter.md

CLAUDE.md                ← Claude Code 项目级桥接
PROJECT_PLAN_v4.md       ← v4.0 项目计划书
fiction-distiller-v4.0-问题清单.md  ← 端到端测试问题清单（含v4.1修复状态）
README.md                ← 本文件
```

## 致谢

感谢真诚、友善、团结、专业的 [LinuxDo 社区](https://linux.do/latest)，让我学到很多 AI 相关的知识和玩法。

> LinuxDo — 学 AI，上 L 站

## 许可

MIT

## 更新日志

详见 [CHANGELOG.md](CHANGELOG.md)

---

**最后更新**: 2026-06-18