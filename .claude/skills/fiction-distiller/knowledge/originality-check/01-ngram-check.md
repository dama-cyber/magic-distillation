---
title: N-gram重合检测
category: originality-check
order: 1
version: 1.0.0
last_updated: 2026-06-18
related_files:
  - originality-check/02-variable-residue.md
  - originality-check/03-human-review.md
  - short-substitution/06-short-pipeline.md
---

# 01-ngram-check：N-gram重合检测

## 1. 什么是N-gram重合

N-gram 是将文本按连续 N 个字切分成的片段。如果原文和新篇有大量相同的 N-gram，说明新篇可能抄袭了原文。

例如：
- 原文："他推开门走进房间"
- 2-gram："他推""推开""开门""门走""走进""进房""房间"
- 3-gram："他推开""推开门""开门走""门走进""走进房""进房间"

## 2. N-gram检测原理

### 2.1 提取原文和新篇的 N-gram

将两篇文章分别切成 N-gram 集合，然后计算交集。

### 2.2 重合率计算

```
N-gram 重合率 = （原文与新篇共有的 N-gram 数 / 新篇总 N-gram 数） × 100%
```

### 2.3 不同 N 值的意义

| N 值 | 检测精度 | 用途 |
|------|----------|------|
| 2-gram | 低，容易误报 | 初步筛查 |
| 3-gram | 中 | 检测常见短语 |
| 5-gram | 较高 | 检测句子片段抄袭 |
| 8-gram | 高 | 检测连续句子抄袭 |
| 12-gram | 很高 | 检测大段抄袭 |

## 3. 目标值

| 指标 | 目标 |
|------|------|
| 2-gram 重合率 | 因语言共性，不单独作为标准 |
| 3-gram 重合率 | < 15% |
| 5-gram 重合率 | **< 5%** |
| 8-gram 重合率 | **0%** |
| 12-gram 重合率 | **0%** |

**核心目标**：5-gram 重合率 < 5%，8-gram 以上完全重合为 0。

## 4. 检测方法

### 4.1 纯中文文本

```python
def get_ngrams(text, n):
    """提取文本中所有 n-gram"""
    text = text.replace('\n', '').replace(' ', '')
    ngrams = []
    for i in range(len(text) - n + 1):
        ngrams.append(text[i:i+n])
    return set(ngrams)

def ngram_overlap(original, new, n):
    """计算 n-gram 重合率"""
    orig_ngrams = get_ngrams(original, n)
    new_ngrams = get_ngrams(new, n)
    overlap = orig_ngrams & new_ngrams
    if not new_ngrams:
        return 0
    return len(overlap) / len(new_ngrams)
```

### 4.2 中英文混合文本

```python
import re

def tokenize(text):
    """将中英文混合文本切分为 token 列表"""
    # 中文字符单独切分
    # 英文按单词切分
    tokens = []
    for char in text:
        if re.match(r'[\u4e00-\u9fff]', char):
            tokens.append(char)
        elif char.isalpha():
            # 累积英文单词
            if tokens and tokens[-1].isalpha():
                tokens[-1] += char
            else:
                tokens.append(char)
        else:
            # 忽略标点
            pass
    return tokens

def get_ngrams_tokens(tokens, n):
    return set(tuple(tokens[i:i+n]) for i in range(len(tokens)-n+1))
```

## 5. 检测注意事项

### 5.1 忽略标点

计算 N-gram 时通常忽略标点符号，只保留文字内容。

### 5.2 忽略对话提示

"他说""她说"等常见对话提示在两篇文章中可能自然重合，应单独处理或降低权重。

### 5.3 通用短语

一些通用短语（如"他看了看""过了一会"）可能自然重合，不应视为抄袭。但如果是连续 8 字以上相同，仍需警惕。

### 5.4 虚词组合

"的""了""是"等虚词组合重合度高，但不代表抄袭。需要结合实词和语义判断。

## 6. 输出报告

```markdown
# N-gram 重合检测报告

## 统计信息
- 原文总字数：____
- 新篇总字数：____
- 新篇总 N-gram 数：____

## 重合率
| N 值 | 重合数 | 重合率 | 目标 | 是否通过 |
|------|--------|--------|------|----------|
| 3-gram |  |  | < 15% |  |
| 5-gram |  |  | < 5% |  |
| 8-gram |  |  | 0% |  |
| 12-gram |  |  | 0% |  |

## 高风险重合片段（5-gram 及以上）
- 片段 1："______"（位置：原文 ___，新篇 ___）
- 片段 2："______"（位置：原文 ___，新篇 ___）

## 结论
- 是否通过：通过 / 未通过
- 未通过项：
- 修正建议：
```

## 7. 修正策略

### 7.1 5-gram 重合偏高

- 找出重合的 5-gram 片段
- 重写包含该片段的句子
- 替换核心动词、名词或场景
- 改变句式结构

### 7.2 8-gram 以上重合

- 必须完全重写该句或该段
- 不能仅做同义词替换
- 必须改变语义结构

## 8. 检查清单

- [ ] 已计算 3-gram、5-gram、8-gram、12-gram 重合率
- [ ] 5-gram 重合率 < 5%
- [ ] 8-gram 以上重合率为 0%
- [ ] 已识别所有高风险重合片段
- [ ] 已重写或修正所有未通过片段
- [ ] 忽略通用短语和虚词组合
