# 知识库全索引

## 三层懒加载优先级

### 🔴 基础层（始终首先加载摘要）
- `general-style/*`     通用分析工具箱
- `author-fingerprint/*` 作者指纹方法论

### 🟡 体裁层（按用户文本类型选择性深入加载）
- `long-fiction/*`      长篇小说
- `short-fiction/*`     短篇小说
- `net-style/*`         网络文学

### 🟢 方法层（创作阶段加载）
- `ai-distillation/*`   蒸馏与原创性验证

## 文件清单

| 文件路径 | 核心内容摘要（一句话） | 关键概念词 | 字数 |
|---------|-------------------|---------|------|
| general-style/01-stylistics | 文学文体学五维度分析框架 | 语域、句法、词汇、修辞、音韵、认知文体学 | ~3500 |
| general-style/02-narratology | 叙事学核心概念与分析方法 | 叙述者分层、叙事时间、聚焦模式、后经典叙事学 | ~3500 |
| general-style/03-rhetoric | 修辞学从象征行动到概念隐喻 | 象征行动、概念隐喻、隐喻文化差异 | ~3500 |
| general-style/04-stylometry | 文体计量学量化分析工具与方法 | 词频统计、聚类分析、作者归因、SVM、BERT | ~3500 |
| general-style/05-imaging | 语言成像理论与感官描写机制 | 名词独立句、蒙太奇、通感神经科学 | ~3500 |
| author-fingerprint/01-lexical | 词汇指纹提取与描述方法 | 高频特征词、词性偏好、词汇密度、语义场 | ~3500 |
| author-fingerprint/02-syntactic | 句式指纹提取与描述方法 | 句长分布、长短句切换、非常规句法 | ~3500 |
| author-fingerprint/03-rhetorical | 修辞指纹提取与描述方法 | 比喻来源域、通感映射、反讽风格、意象谱系 | ~3500 |
| author-fingerprint/04-narrative-voice | 叙事声音指纹提取与描述方法 | 叙述者类型、不可靠叙述、性别编码 | ~3500 |
| author-fingerprint/05-punctuation | 标点指纹提取与描述方法 | 破折号、省略号、引号、呼吸节奏 | ~3500 |
| author-fingerprint/06-cross-work | 跨作品风格一致性与演变分析 | 风格核心、风格表层、演变驱动因素 | ~3500 |
| net-style/01-genres | 网文流派分类体系与边界 | 玄幻、仙侠、无限流、系统流、流派融合 | ~3500 |
| net-style/02-pleasure-mechanism | 网文爽点机制与心理学基础 | 力量型/地位型/情感型/认知型爽点、多巴胺 | ~3500 |
| net-style/03-world-building | 网文世界观设定模式与架构 | 阶梯式/网格式/层叠式/生态式、三层嵌套 | ~3500 |
| net-style/04-characters | 网文人设角色与金手指设计 | 功能角色、金手指类型、配角生态 | ~3500 |
| net-style/05-rhythm-structure | 网文节奏结构与断章技巧 | 黄金三章、章节钩子、高潮间隔 | ~3500 |
| net-style/06-narrative-focus | 网文叙事重心与情感策略 | 男频女频差异、共情机制、情感节奏 | ~3500 |
| net-style/07-era-features | 网文时代特征与演变脉络 | BBS时代、付费阅读、免费阅读、海外传播 | ~3500 |
| long-fiction/01-story-layer | 长篇情节冲突模型与编排 | 冲突类型、多线冲突、冲突递进 | ~3500 |
| long-fiction/02-narrative-layer | 长篇叙述层面与聚焦模式 | 自由间接引语、叙事时间、意识流 | ~3500 |
| long-fiction/03-structure | 长篇结构设计与多线交织 | 起承转合、非线性结构、章回体 | ~3500 |
| long-fiction/04-style | 长篇文体层面与象征系统 | 五感权重、隐喻系统、象征建立与回收 | ~3500 |
| long-fiction/05-revision | 长篇修改打磨与节奏调控 | 结构性修改、局部修改、删减与强化 | ~3500 |
| short-fiction/01-elements | 短篇唯一效果原则与冰山理论 | 爱伦坡效应、留白、东西方美学差异 | ~3500 |
| short-fiction/02-strategic-choice | 短篇战略选择与顿悟设计 | 契诃夫细节法、细节密度、顿悟时刻 | ~3500 |
| short-fiction/03-details | 短篇细节真实与感官分配 | 三重标准、密度-速度对应、展示vs讲述 | ~3500 |
| short-fiction/04-structure | 短篇结构设计与结尾类型 | 欲望+障碍+行动、六种结尾、闪小说 | ~3500 |
| short-fiction/05-three-beauties | 短篇美学边界与诗歌对话 | 自由、想象、超越、闪小说极限压缩 | ~3500 |
| ai-distillation/01-feature-extraction | 文本特征提取技术与新范式 | TF-IDF、词嵌入、BERT、提示驱动提取 | ~3500 |
| ai-distillation/02-fingerprint-verification | 风格指纹验证与法律边界 | 作者归因、对抗性攻击、AI检测 | ~3500 |
| ai-distillation/03-imitation-strategies | AI风格模仿策略与方法 | 提示工程、少样本/零样本、RAG、风格向量 | ~3500 |
| ai-distillation/04-evaluation | 原创性评估与伦理边界 | 分类器评估、人类盲测、可解释性、伦理原则 | ~3500 |

## 知识图谱：跨文件关联

```
general-style/01-stylistics ──→ author-fingerprint/01-lexical
    │                              │
    ├──→ general-style/02-narratology ──→ author-fingerprint/04-narrative-voice
    │                              │
    ├──→ general-style/03-rhetoric ──→ author-fingerprint/03-rhetorical
    │                              │
    ├──→ general-style/04-stylometry ──→ ai-distillation/01-feature-extraction
    │                              │
    └──→ general-style/05-imaging ──→ author-fingerprint/03-rhetorical (通感)

net-style/01-genres ──→ net-style/02-pleasure-mechanism ──→ net-style/05-rhythm-structure
    │                          │
    ├──→ net-style/03-world-building ──→ long-fiction/03-structure
    │
    ├──→ net-style/04-characters ──→ author-fingerprint/04-narrative-voice
    │
    ├──→ net-style/06-narrative-focus ──→ net-style/02-pleasure-mechanism
    │
    └──→ net-style/07-era-features ──→ ai-distillation/03-imitation-strategies

long-fiction/01-story-layer ──→ long-fiction/02-narrative-layer ──→ long-fiction/03-structure
    │                                                              │
    └──→ long-fiction/04-style ──→ long-fiction/05-revision        │
                                                                   │
short-fiction/01-elements ──→ short-fiction/02-strategic-choice ──→ short-fiction/04-structure
    │                              │
    └──→ short-fiction/03-details ──→ short-fiction/05-three-beauties

ai-distillation/01-feature-extraction ──→ ai-distillation/02-fingerprint-verification
    │                                           │
    └──→ ai-distillation/03-imitation-strategies ──→ ai-distillation/04-evaluation
```

## 搜索覆盖率报告

- 已覆盖主题数：32 个（基础 32）
- 动态扩展新增主题数：8 个（无限流/诸天流、克苏鲁网文、轻小说本土化、网文海外传播、AI写网文、文体计量学工具、风格迁移AI、认知文体学）

