"""
word_count_analyzer.py
原文字数结构分析工具
输出：字数预算表 JSON
"""

import re
import json
import sys
from pathlib import Path
from encoding_utils import read_text_safe


def count_chinese_chars(text):
    """统计中文字符数（不含标点）"""
    return len(re.findall(r'[\u4e00-\u9fff]', text))


def count_all_chars(text):
    """统计所有字符数（含标点、数字、字母）"""
    return len(text)


def split_sentences(text):
    """按中文句末标点分句"""
    sentences = re.split(r'[。！？…]+', text)
    return [s.strip() for s in sentences if s.strip()]


def split_paragraphs(text):
    """按逻辑段落分割（智能合并网文单句段）
    
    策略：
    1. 先按空行分割为逻辑段落
    2. 对没有空行的文本，将连续的非空行合并为逻辑段落
    3. 合并条件：相邻行合计字数低于MIN_PARAGRAPH_CHARS时合并
    """
    MIN_PARAGRAPH_CHARS = 80
    
    if '\n\n' in text or '\r\n\r\n' in text:
        paragraphs = re.split(r'\n\s*\n', text)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        return paragraphs
    
    lines = text.split('\n')
    paragraphs = []
    current_para = []
    current_chars = 0
    
    for line in lines:
        line = line.strip()
        if not line:
            if current_para:
                paragraphs.append('\n'.join(current_para))
                current_para = []
                current_chars = 0
            continue
        
        line_chars = count_chinese_chars(line)
        
        if current_para and current_chars + line_chars < MIN_PARAGRAPH_CHARS:
            current_para.append(line)
            current_chars += line_chars
        else:
            if current_para:
                paragraphs.append('\n'.join(current_para))
            current_para = [line]
            current_chars = line_chars
    
    if current_para:
        paragraphs.append('\n'.join(current_para))
    
    return [p for p in paragraphs if p.strip()]


def classify_sentence_length(sentence):
    """分类句长"""
    length = count_chinese_chars(sentence)
    if length <= 15:
        return 'short'
    elif length <= 30:
        return 'medium'
    else:
        return 'long'


def extract_dialogue(text):
    """提取对话内容（支持中文引号 "" 和 '' 以及英文引号）"""
    # 中文双引号 \u201c \u201d，中文单引号 \u2018 \u2019
    dialogue = []
    dialogue.extend(re.findall(r'[\u201c]([^\u201d]+)[\u201d]', text))  # 中文双引号
    dialogue.extend(re.findall(r'[\u2018]([^\u2019]+)[\u2019]', text))  # 中文单引号
    dialogue.extend(re.findall(r'[""]([^""]+)[""]', text))  # 英文双引号
    dialogue.extend(re.findall(r"['']([^'']+)['']", text))  # 英文单引号
    dialogue.extend(re.findall(r'[\u300c]([^\u300d]+)[\u300d]', text))  # 中文角括号「」
    dialogue.extend(re.findall(r'[\u300e]([^\u300f]+)[\u300f]', text))  # 中文双角括号『』
    return dialogue


def analyze_text(text):
    """分析文本结构"""
    paragraphs = split_paragraphs(text)
    sentences = split_sentences(text)
    dialogue_parts = extract_dialogue(text)

    total_chars = count_chinese_chars(text)
    total_all = count_all_chars(text)

    paragraph_data = []
    for i, p in enumerate(paragraphs, 1):
        p_sentences = split_sentences(p)
        p_dialogue = extract_dialogue(p)
        dialogue_chars = sum(count_chinese_chars(d) for d in p_dialogue)
        p_chars = count_chinese_chars(p)
        paragraph_data.append({
            'index': i,
            'chars': p_chars,
            'chars_all': count_all_chars(p),
            'sentences': len(p_sentences),
            'dialogue_chars': dialogue_chars,
            'dialogue_ratio': round(dialogue_chars / p_chars, 4) if p_chars > 0 else 0
        })

    sentence_lengths = [count_chinese_chars(s) for s in sentences]
    length_distribution = {
        'short': sum(1 for s in sentences if classify_sentence_length(s) == 'short'),
        'medium': sum(1 for s in sentences if classify_sentence_length(s) == 'medium'),
        'long': sum(1 for s in sentences if classify_sentence_length(s) == 'long')
    }
    total_sentences = len(sentences)
    if total_sentences > 0:
        length_distribution = {
            k: round(v / total_sentences, 4)
            for k, v in length_distribution.items()
        }

    dialogue_chars = sum(count_chinese_chars(d) for d in dialogue_parts)
    dialogue_ratio = round(dialogue_chars / total_chars, 4) if total_chars > 0 else 0

    # 估算叙述和描写比例（简化版）
    # 叙述：非对话、非明显描写句
    # 描写：包含大量形容词或感官词的句子
    narration_chars = total_chars - dialogue_chars
    description_chars = 0
    for s in sentences:
        if not re.search(r'["""]', s):
            # 简单规则：如果句子包含感官词或形容词密度高，算作描写
            sensory_words = re.findall(r'[看听闻摸感觉冷暖湿光亮暗色]', s)
            adj_markers = re.findall(r'[的得地]', s)
            if len(sensory_words) >= 2 or len(adj_markers) >= 3:
                description_chars += count_chinese_chars(s) * 0.6

    narration_chars = max(0, narration_chars - description_chars)
    narration_ratio = round(narration_chars / total_chars, 4) if total_chars > 0 else 0
    description_ratio = round(description_chars / total_chars, 4) if total_chars > 0 else 0

    return {
        'total_chars': total_chars,
        'total_chars_all': total_all,
        'paragraph_count': len(paragraphs),
        'sentence_count': len(sentences),
        'sentence_lengths': sentence_lengths,
        'sentence_length_distribution': length_distribution,
        'paragraphs': paragraph_data,
        'dialogue_ratio': dialogue_ratio,
        'narration_ratio': narration_ratio,
        'description_ratio': description_ratio,
        'mean_sentence_length': round(sum(sentence_lengths) / len(sentence_lengths), 2) if sentence_lengths else 0,
        'std_sentence_length': round(__import__('statistics').stdev(sentence_lengths), 2) if len(sentence_lengths) > 1 else 0
    }


def generate_budget_table(analysis, target_total=None, tolerance=0.05):
    """生成字数预算表"""
    total = analysis['total_chars']
    if target_total is None:
        target_total = total

    budget = []
    for p in analysis['paragraphs']:
        ratio = p['chars'] / total if total > 0 else 0
        target_chars = int(target_total * ratio)
        min_chars = int(target_chars * (1 - tolerance))
        max_chars = int(target_chars * (1 + tolerance))
        budget.append({
            'index': p['index'],
            'original_chars': p['chars'],
            'ratio': round(ratio, 4),
            'target_chars': target_chars,
            'min_chars': min_chars,
            'max_chars': max_chars,
            'dialogue_ratio': p['dialogue_ratio']
        })

    return {
        'original_total': total,
        'target_total': target_total,
        'tolerance': tolerance,
        'paragraphs': budget
    }


def main():
    if len(sys.argv) < 2:
        print("用法: python word_count_analyzer.py <原文文件.md> [输出文件.json]")
        sys.exit(1)

    input_file = Path(sys.argv[1])
    output_file = Path(sys.argv[2]) if len(sys.argv) > 2 else input_file.with_suffix('.analysis.json')

    text = read_text_safe(input_file)
    # 移除 YAML frontmatter（如果有）
    if text.startswith('---'):
        parts = text.split('---', 2)
        if len(parts) >= 3:
            text = parts[2]

    analysis = analyze_text(text)
    budget = generate_budget_table(analysis)

    result = {
        'analysis': analysis,
        'budget': budget
    }

    output_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"分析完成：{output_file}")
    print(f"原文总字数：{analysis['total_chars']}")
    print(f"段落数：{analysis['paragraph_count']}")
    print(f"句子数：{analysis['sentence_count']}")
    print(f"对话占比：{analysis['dialogue_ratio']:.2%}")


if __name__ == '__main__':
    main()
