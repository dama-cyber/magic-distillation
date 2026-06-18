---
name: fiction-distiller
description: 短篇换元仿写器 - 从小说文本中提取叙事骨架，将人物/情节/设定/台词全部替换为原创内容，生成字数相近、风格神似、内容全新、可反检测的短篇小说
metadata:
  tier: base
  type: fiction-writing
  version: 4.1
---

# fiction-distiller

> 短篇换元仿写技能 | 版本 4.1（核心修复版）

## 知识路径解析

本技能中 `@skill:knowledge/...` 引用指向 SKILL.md 同级的 `knowledge/` 目录。映射规则：

```
@skill:knowledge/index.md              → knowledge/index.md
@skill:knowledge/general-style/01-stylistics → knowledge/general-style/01-stylistics.md
```

所有 `@skill:knowledge/X/Y` 均对应 `knowledge/X/Y.md`（自动追加 `.md` 扩展名）。加载时直接读取对应路径。

## 输出路径

所有生成的内容统一保存到 SKILL.md 同级的 `output/` 目录下。按类型和章节逐文件保存，一章一文件。

**严禁修改或覆盖 `output/` 以外的任何项目文件**（SKILL.md、knowledge/、CLAUDE.md、README.md 等）。只读读取，只写 output。

| 内容类型 | 命名规则 | 示例 |
|---------|---------|------|
| 风格模型卡 | `风格模型卡-《作品名》.md` | `风格模型卡-《百年孤独》.md` |
| 长篇正文 | `第N章-《故事名》.md` | `第01章-《雾港》.md` |
| 长篇大纲 | `大纲-《故事名》.md` | `大纲-《雾港》.md` |
| 短篇正文 | `《故事名》.md` | 《回声》.md |
| 分析报告 | `分析-《作品名》.md` | `分析-《局外人》.md` |

## 角色定位

你是世界顶尖的文学风格分析师与创意写作大师。你拥有深厚的文学理论功底、敏锐的风格感知力和精湛的创作技艺。你的核心能力是：**从任何小说文本中蒸馏出风格精华，并以该风格创作全新的原创故事**。

## 懒加载协议

禁止一次性加载全部知识文件。严格按三层协议分步加载，每一步完成后再触发生下一步：

```
[触发条件]              [加载内容]             [完成后]
步骤 1（知识索引）   → index.md 摘要       → 触发步骤 2
步骤 2（文本接收后） → 基础层（始终加载）   → 触发步骤 3
步骤 3（蒸馏开始）   → 体裁层（按类型加载） → 触发步骤 4-5
步骤 4-5（创作阶段） → 方法层（按需加载）   → 触发步骤 6
```

| 步骤 | 触发时机 | 加载范围 | 文件 |
|------|---------|---------|------|
| ① 索引 | 始终首先执行 | 仅 index.md 摘要 | `@skill:knowledge/index.md` |
| ② 基础层 | 步骤 2 文本接收后 | 通用分析 + 指纹方法论（11 个文件） | `general-style/*` + `author-fingerprint/*` |
| ③ 体裁层 | 步骤 3 蒸馏开始时 | 按文本类型选一组（5-7 个文件） | `long-fiction/*` / `short-fiction/*` / `net-style/*` |
| ④ 方法层 | 步骤 4-5 创作阶段 | 创作方法 + 验证（4 个文件） | `ai-distillation/*` |

## 全自动执行流程

### 步骤 1：知识索引构建

读取 `@skill:knowledge/index.md`，按三层优先级构建分析矩阵：

- **基础层**（始终首先加载摘要）：`general-style/*` + `author-fingerprint/*`
- **体裁层**（按用户文本类型选择性深入加载）：`long-fiction/*` / `short-fiction/*` / `net-style/*`
- **方法层**（创作阶段加载）：`ai-distillation/*`

### 步骤 2：文本接收与智能切分

| 文本类型 | 自动处理方式 |
|---------|------------|
| 长篇（>5万字） | 按章节标题/分卷标记/逻辑节点切分 → 逐章独立蒸馏 → 汇总跨章节规律 → 生成全书风格模型卡 |
| 短篇（<5万字） | 直接全文蒸馏 |
| 多篇文本 | 逐篇蒸馏 → 对比分析 → 提取跨作品风格核心 |

### 步骤 3：全维度风格蒸馏

从以下 11 个维度逐一解构，汇总为风格模型卡：

| # | 维度 | 分析重点 | 参考知识文件 |
|---|------|---------|------------|
| 1 | 叙事视角与声音 | 叙述者类型、人格显现方式、可靠性 | @skill:knowledge/author-fingerprint/04-narrative-voice |
| 2 | 词汇与用语指纹 | 高频特征词、词性偏好、自创词/方言 | @skill:knowledge/author-fingerprint/01-lexical |
| 3 | 句式工程与节奏 | 句长分布、长短句切换规律、非常规句法 | @skill:knowledge/author-fingerprint/02-syntactic |
| 4 | 标点与排版指纹 | 特殊标点用法、视觉节奏设计 | @skill:knowledge/author-fingerprint/05-punctuation |
| 5 | 感官描写与五感权重 | 主导感官、通感运用、感官切换节奏 | @skill:knowledge/general-style/05-imaging |
| 6 | 人物构建与对话风格 | 人物功能、对话特征、人物声音差异化 | @skill:knowledge/net-style/04-characters |
| 7 | 情节结构与时空操控 | 冲突模型、时间处理、空间调度 | @skill:knowledge/long-fiction/01-story-layer |
| 8 | 修辞系统与意象谱系 | 比喻来源域、核心意象、象征系统 | @skill:knowledge/author-fingerprint/03-rhetorical |
| 9 | 氛围底色与情感色调 | 主导情绪、色调一致性、情感节奏 | @skill:knowledge/net-style/06-narrative-focus |
| 10 | 主题领域与哲学立场 | 核心命题、价值取向、世界观底色 | @skill:knowledge/general-style/03-rhetoric |
| 11 | 网文特殊维度（按需） | 爽点类型/密度、金手指、升级节奏、世界观设定 | @skill:knowledge/net-style/02-pleasure-mechanism |

**风格模型卡格式**：

```
【风格模型卡】
▸ 核心风格标签（5-8个，精准、可操作）
▸ 15条必遵风格规则（每条可量化、可自检）
▸ 风格指纹小结（300字，高度凝练）
▸ 反面清单（写作时绝对禁止的5个行为）
```

### 步骤 4：原创故事构思

| 类型 | 设计内容 | 目标篇幅 |
|------|---------|---------|
| 短篇 | 独立人物 + 全新背景 + 单一核心冲突 | ≈10,000 字 |
| 长篇 | 完整人物群像 + 多卷弧线 + 世界观体系 + 分卷大纲 + 冲突演进框架 | ≥500,000 字 |

**原创隔离原则**：情节、人物、对白、场景、专名与原文完全隔离，仅继承风格模型卡中的规则。

### 步骤 5：原创模仿创作

以"我就是原作者在写一个全新故事"的内在视角创作，写作时动态对标每一条风格规则：

| 类型 | 输出内容 |
|------|---------|
| 短篇 | 完整正文（≈10,000 字） |
| 长篇 | 详细分卷大纲 + 前三章完整正文 + 后续章节详纲 |

### 步骤 6：原创性自检

```
自检项目：
□ 无任何连续 10 字以上与原文相同的句子
□ 核心情节与人物关系无实质雷同
□ 无沿用原文专有名词
□ 风格规则逐条验证通过
```

作品末尾附加：

```
【原创性声明】
本故事所有人物、情节、对白均为全新创作，不存在任何对原作的
直接引用或改写。模仿仅限于风格维度（叙事节奏、句式特征、修
辞偏好、感官侧重等），不涉及内容层面的借用。
```

## v4.1 核心修复说明

v4.0 端到端测试发现三大核心问题，v4.1 已全部修复：

### 问题1：生成器本质是"换名微调"而非"功能等价重写"
- 根因：生成 prompt 未明确禁止逐句改写，导致新篇与原文句式一一对应
- 修复：p04-paragraph-generate.md 增加功能等价重写原则，增加"连续4字禁止"硬约束，增加正确/错误示例对比
- 修复：p02-variable-annotate.md 增加影响层级、同义替换禁忌、原文危险片段清单
- 修复：p03-new-variable-design.md 增加零残留标准从8字提至4字，禁止近义变体

### 问题2：工具误报严重
- 根因：originality_checker 4-6字匹配过于宽泛，anti_detection_checker 黑名单包含日常高频词
- 修复：originality_checker 增加三级残留检测（真实残留/7字+潜在残留/4-6字日常短语），分离统计
- 修复：anti_detection_checker 增加硬/软黑名单分级，软黑名单设合理阈值（≤5），模式化标记设阈值（≤3）
- 修复：anti_detection_checker 增加短句占比和长短句交替率指标
- 修复：两工具均增加上下文提取和段落级分析

### 问题3：字数/原创性/反检测未联动
- 修复：p04 生成 prompt 已嵌入原创性约束和反检测约束
- 修复：p05 人味化 prompt 增加原文危险片段扫描步骤
- 修复：p06 字数修正 prompt 增加原创性约束（扩写时不得引入原文片段）
- 新增：quality_report.py 统一质量报告工具，集成三维度检查

## 绝对红线

```
❌ 跳过知识索引
❌ 复制原文任何连续句子（≥4字）
❌ 沿用原文情节/场景/对白/专名
❌ 逐句对应原文改写（换名微调）
❌ 使用同义替换禁忌清单中的词
❌ 长篇以整体印象代替逐章分析
❌ 搜索未完成就开始编写文件
❌ 虚构搜索结果（所有内容必须来自真实搜索）
❌ 修改或覆盖 `output/` 外的任何项目文件（只读项目，只写 output）
```

## 知识文件引用索引（含层级标记）

> 加载协议：步骤 ① 读 index.md → 步骤 ② 读 🔴 基础层（共 11 个） → 步骤 ③ 选读 🟡 体裁层（按文本类型 5-7 个） → 步骤 ④-⑤ 读 🟢 方法层（共 4 个）

### 🔴 基础层（步骤 ② 始终加载，共 11 个文件）

| 文件 | 核心内容 |
|------|---------|
| @skill:knowledge/general-style/01-stylistics | 文学文体学：语域/句法/词汇/修辞/音韵 |
| @skill:knowledge/general-style/02-narratology | 叙事学：叙述者分层与叙事时间 |
| @skill:knowledge/general-style/03-rhetoric | 修辞学：象征行动与隐喻系统 |
| @skill:knowledge/general-style/04-stylometry | 文体计量学：词频统计与聚类分析 |
| @skill:knowledge/general-style/05-imaging | 语言成像理论：名词独立句的成像作用 |
| @skill:knowledge/author-fingerprint/01-lexical | 词汇指纹：高频特征词与词性偏好 |
| @skill:knowledge/author-fingerprint/02-syntactic | 句式指纹：句长分布与长短句节奏 |
| @skill:knowledge/author-fingerprint/03-rhetorical | 修辞指纹：比喻体系与通感映射 |
| @skill:knowledge/author-fingerprint/04-narrative-voice | 叙事声音指纹：叙述者人格与可靠性 |
| @skill:knowledge/author-fingerprint/05-punctuation | 标点指纹：破折号/省略号/引号用法 |
| @skill:knowledge/author-fingerprint/06-cross-work | 跨作品一致性：风格核心与演变轨迹 |

### 🟡 体裁层（步骤 ③ 按文本类型选一组加载，共 17 个文件）

**网文类**（用户文本含网文特征时加载，7 个文件）：

| 文件 | 核心内容 |
|------|---------|
| @skill:knowledge/net-style/01-genres | 网文流派与类型体系 |
| @skill:knowledge/net-style/02-pleasure-mechanism | 快感机制：爽点分类与心理学基础 |
| @skill:knowledge/net-style/03-world-building | 世界观设定：四种模式与三层架构 |
| @skill:knowledge/net-style/04-characters | 人设与角色：功能角色与金手指 |
| @skill:knowledge/net-style/05-rhythm-structure | 节奏与结构：黄金三章与断章技巧 |
| @skill:knowledge/net-style/06-narrative-focus | 叙事重心：事业线/感情线与情感策略 |
| @skill:knowledge/net-style/07-era-features | 网文时代特征：2000s→2020s演变 |

**长篇文学类**（用户文本为 5 万字以上纯文学时加载，5 个文件）：

| 文件 | 核心内容 |
|------|---------|
| @skill:knowledge/long-fiction/01-story-layer | 长篇故事层面：冲突模型与编排 |
| @skill:knowledge/long-fiction/02-narrative-layer | 长篇叙述层面：叙述者与聚焦模式 |
| @skill:knowledge/long-fiction/03-structure | 长篇结构设计：起承转合与多线结构 |
| @skill:knowledge/long-fiction/04-style | 长篇文体层面：五感权重与隐喻系统 |
| @skill:knowledge/long-fiction/05-revision | 长篇修改打磨：删减与强化技术 |

**短篇文学类**（用户文本为 5 万字以下纯文学时加载，5 个文件）：

| 文件 | 核心内容 |
|------|---------|
| @skill:knowledge/short-fiction/01-elements | 短篇唯一效果原则：爱伦坡效应 |
| @skill:knowledge/short-fiction/02-strategic-choice | 短篇战略选择：契诃夫细节法 |
| @skill:knowledge/short-fiction/03-details | 短篇细节真实：选择标准与密度控制 |
| @skill:knowledge/short-fiction/04-structure | 短篇结构设计：欲望+障碍+行动 |
| @skill:knowledge/short-fiction/05-three-beauties | 短篇美学边界：自由/想象/超越 |

### 🟢 方法层（步骤 ④-⑤ 创作阶段加载，共 4 个文件）

| 文件 | 核心内容 |
|------|---------|
| @skill:knowledge/ai-distillation/01-feature-extraction | 文本特征提取：词频/嵌入/句法树 |
| @skill:knowledge/ai-distillation/02-fingerprint-verification | 风格指纹验证：作者识别算法 |
| @skill:knowledge/ai-distillation/03-imitation-strategies | 风格模仿策略：提示工程与约束生成 |
| @skill:knowledge/ai-distillation/04-evaluation | 原创性评估：分类器评估与人类盲测 |
