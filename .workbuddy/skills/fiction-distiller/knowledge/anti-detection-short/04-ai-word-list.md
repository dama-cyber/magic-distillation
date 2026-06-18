---
title: AI特征词与模式化标记黑名单
category: anti-detection-short
order: 4
version: 1.0.0
last_updated: 2026-06-18
related_files:
  - anti-detection-short/01-detection-principles.md
  - anti-detection-short/02-humanization.md
  - anti-detection-short/05-short-verification.md
---

# 04-ai-word-list：AI特征词与模式化标记黑名单

## 1. 什么是AI特征词

AI 特征词是 AI 模型在生成文本时偏好使用的词汇和表达。这些词本身没有问题，但高密度出现会让文本被检测工具识别为 AI 生成。

**重要原则**：
- 不是禁用这些词
- 是避免高密度、模式化地使用这些词
- 在特定语境中，这些词可以自然出现

## 2. 英文AI特征词黑名单

### 2.1 连接/过渡词（高频）

- furthermore
- moreover
- additionally
- consequently
- therefore
- thus
- hence
- nonetheless
- nevertheless
- notwithstanding
- in addition
- as a result
- for instance
- for example
- in particular
- specifically

### 2.2 抽象/学术动词

- delve
- explore
- navigate
- unravel
- dissect
- examine
- scrutinize
- underscore
- highlight
- illuminate
- elucidate
- shed light on
- pave the way

### 2.3 华丽/文学化词汇（AI 堆砌）

- tapestry
- mosaic
- kaleidoscope
- symphony
- dance
- intricate
- nuanced
- multifaceted
- vibrant
- dynamic
- robust
- poignant
- evocative
- ethereal
- whimsical

### 2.4 总结/框架词

- in conclusion
- to summarize
- to conclude
- in summary
- ultimately
- overall
- all in all
- taking everything into account
- on the whole

### 2.5 评价/强化词

- pivotal
- crucial
- essential
- significant
- paramount
- imperative
- indispensable
- profound
- remarkable
- notable

### 2.6 其他AI常见表达

- it's important to note that
- it's worth mentioning that
- as mentioned earlier
- as previously discussed
- in the ever-evolving landscape of
- in today's world
- a testament to
- a reflection of
- serve as a reminder

## 3. 中文AI特征词黑名单

### 3.1 过渡/框架词

- 首先…其次…再次…最后
- 第一…第二…第三…
- 综上所述
- 总而言之
- 归根结底
- 由此可见
- 因此
- 故而
- 于是乎

### 3.2 总结/升华词

- 不可否认的是
- 值得注意的是
- 令人深思的是
- 从某种意义上说
- 从另一个角度来看
- 这不禁让人想到
- 留给我们的启示是
- 深刻地揭示了

### 3.3 模式化表达

- 不仅…而且…（过度使用）
- 既…又…（过度使用）
- 一边…一边…（过度使用）
- 有的…有的…（过度使用）
- 正如…所说
- 就像…一样
- 仿佛…一般

### 3.4 书面化/抽象词

- 进行一个…
- 开展一项…
- 产生了一种…
- 形成了一种…
- 体现了一种…
- 表达了一种…
- 展现了一种…

### 3.5 高频形容词

- 深刻的
- 重要的
- 关键的
- 核心的
- 根本的
- 深远的
- 巨大的
- 显著的

### 3.6 网文AI痕迹词

- 且说
- 话说
- 却说
- 只见
- 忽闻
- 蓦然
- 刹那间
- 顿时间
- 一时间（过度使用）
- 不由得
- 不禁
- 下意识
- 莫名
- 仿佛冥冥之中

## 4. 模式化标记黑名单

### 4.1 结构模式

- 每段开头都是"他/她/它"
- 连续三段以上结构相同
- 结尾段都是总结 + 升华
- 对话模式完全规整（问-答-问-答）
- 每段结尾都有过渡到下一段的句子

### 4.2 逻辑模式

- 过度平滑的因果关系
- 所有问题都有解释
- 所有伏笔都明确回收
- 情绪变化过于线性
- 人物动机过于清晰

### 4.3 表达模式

- 排比句过度使用
- 对偶句过度使用
- 比喻密度过高（每段超过 2 个）
- 成语堆砌
- 四字词语堆砌

## 5. 扫描规则

### 5.1 命中判定

- 英文特征词：出现即命中（但如果出现在人物对话中可忽略）
- 中文特征词：出现即命中（但成语在对话中可忽略）
- 模式化标记：连续出现 3 次以上即命中

### 5.2 例外情况

以下情况可以忽略：
- 出现在人物对话中（符合人物身份）
- 出现在特定文体中（如书信、公文）
- 单次出现，且上下文自然

## 6. 替换建议

### 6.1 英文替换

| AI 特征词 | 替换方案 |
|-----------|----------|
| furthermore | 另外 / 而且 / 再说 |
| delve | 深入 / 探究 / 翻看 |
| tapestry | 图景 / 画面 / 故事 |
| in conclusion | 结尾不留这个词 |
| pivotal | 关键 / 重要 |
| underscore | 强调 / 突出 / 说明 |

### 6.2 中文替换

| AI 特征词 | 替换方案 |
|-----------|----------|
| 综上所述 | 删除，或用细节代替 |
| 不可否认的是 | 删除，或改为"确实" |
| 值得注意的是 | 删除，直接写细节 |
| 首先…其次…最后 | 改为自然叙述 |
| 不仅…而且… | 改为两个独立句子 |
| 深刻地揭示了 | 改为具体细节呈现 |

## 7. 检测工具扫描逻辑

```python
def scan_ai_words(text):
    ai_words = []
    for word in AI_WORD_BLACKLIST:
        if word in text and not in_dialogue(text, word):
            ai_words.append(word)
    return ai_words

def scan_patterns(text):
    patterns = []
    # 检查连续三段以上结构相同
    if has_repeated_paragraph_structure(text, n=3):
        patterns.append("连续三段结构相同")
    # 检查结尾总结段
    if has_summary_ending(text):
        patterns.append("结尾总结升华")
    # 检查过度排比
    if has_excessive_parallelism(text):
        patterns.append("过度排比")
    return patterns
```

## 8. 检查清单

- [ ] 扫描英文 AI 特征词，命中 0
- [ ] 扫描中文 AI 特征词，命中 0
- [ ] 扫描模式化结构，命中 0
- [ ] 检查对话中的特征词是否符合人物身份
- [ ] 确保没有过度使用排比、对偶
- [ ] 确保结尾没有刻意总结或升华
- [ ] 确保过渡自然，不使用框架化连接词
