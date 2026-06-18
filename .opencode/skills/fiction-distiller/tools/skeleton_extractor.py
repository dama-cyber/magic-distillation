"""
skeleton_extractor.py v2.0
五维骨架提取工具 —— 规则型骨架卡
从原文提取"写法规则"和"变异许可"，而非复制段落结构
"""

import re
import json
import sys
from pathlib import Path
import statistics
from encoding_utils import read_text_safe


def count_chinese_chars(text):
    return len(re.findall(r'[\u4e00-\u9fff]', text))


def split_sentences(text):
    sentences = re.split(r'[。！？…]+', text)
    return [s.strip() for s in sentences if s.strip()]


def split_paragraphs(text):
    if '\n\n' in text or '\r\n\r\n' in text:
        paragraphs = re.split(r'\n\s*\n', text)
    else:
        lines = text.split('\n')
        paragraphs = []
        current = []
        for line in lines:
            stripped = line.strip()
            if not stripped:
                if current:
                    paragraphs.append('\n'.join(current))
                    current = []
                continue
            current.append(stripped)
        if current:
            paragraphs.append('\n'.join(current))
    return [p.strip() for p in paragraphs if p.strip()]


def classify_sentence_length(sentence):
    length = count_chinese_chars(sentence)
    if length <= 10:
        return '短'
    elif length <= 25:
        return '中'
    else:
        return '长'


def compute_rhythm(text):
    paragraphs = split_paragraphs(text)
    sentences = split_sentences(text)

    para_lengths = [count_chinese_chars(p) for p in paragraphs]
    sent_lengths = [count_chinese_chars(s) for s in sentences]

    para_dist = {'极短': 0, '短': 0, '中': 0, '长': 0, '极长': 0}
    for pl in para_lengths:
        if pl < 50:
            para_dist['极短'] += 1
        elif pl < 200:
            para_dist['短'] += 1
        elif pl < 500:
            para_dist['中'] += 1
        elif pl < 1000:
            para_dist['长'] += 1
        else:
            para_dist['极长'] += 1

    para_dist = {k: round(v / len(paragraphs), 2) if paragraphs else 0 for k, v in para_dist.items()}

    short_count = sum(1 for s in sentences if count_chinese_chars(s) <= 10)
    medium_count = sum(1 for s in sentences if 10 < count_chinese_chars(s) <= 25)
    long_count = sum(1 for s in sentences if count_chinese_chars(s) > 25)
    total = len(sentences)

    sent_dist = {
        '短句': round(short_count / total, 2) if total else 0,
        '中句': round(medium_count / total, 2) if total else 0,
        '长句': round(long_count / total, 2) if total else 0
    }

    mean_len = statistics.mean(sent_lengths) if sent_lengths else 0
    std_len = statistics.stdev(sent_lengths) if len(sent_lengths) > 1 else 0
    burstiness = round(std_len / mean_len, 4) if mean_len > 0 else 0

    return {
        'paragraph_length_distribution': para_dist,
        'sentence_length_distribution': sent_dist,
        'mean_sentence_length': round(mean_len, 1),
        'std_sentence_length': round(std_len, 1),
        'burstiness': burstiness,
    }


def compute_language_features(text):
    total_chars = count_chinese_chars(text)
    dialogue_chars = sum(count_chinese_chars(m.group(1)) for m in re.finditer(r'[""""]([^""""]+)[""""]', text))
    dialogue_ratio = round(dialogue_chars / total_chars, 4) if total_chars > 0 else 0

    dash_count = text.count('——')
    ellipsis_count = text.count('……')
    semicolon_count = text.count('；')
    exclamation_count = text.count('！')
    question_count = text.count('？')

    de_count = text.count('的')
    de_density = round(de_count / total_chars, 4) if total_chars > 0 else 0

    return {
        'dialogue_ratio': dialogue_ratio,
        'narration_ratio': round(1 - dialogue_ratio, 4),
        'special_punctuation': {
            'dash': dash_count,
            'ellipsis': ellipsis_count,
            'semicolon': semicolon_count,
            'exclamation': exclamation_count,
            'question': question_count
        },
        'de_density': de_density
    }


def create_skeleton_card(text):
    """创建规则型骨架卡（v2.0）"""
    paragraphs = split_paragraphs(text)
    sentences = split_sentences(text)
    rhythm = compute_rhythm(text)
    language = compute_language_features(text)
    total_chars = count_chinese_chars(text)

    # v5.0：计算当前文本的方差比，作为参考
    para_lengths = [count_chinese_chars(p) for p in paragraphs]
    max_len = max(para_lengths) if para_lengths else 1
    min_len = min(para_lengths) if para_lengths else 1
    current_ratio = round(max_len / max(min_len, 1), 1)

    # v5.0：计算当前超短句和超长句数量
    micro_count = sum(1 for s in sentences if count_chinese_chars(s) <= 3)
    mega_count = sum(1 for s in sentences if count_chinese_chars(s) >= 50)

    skeleton = {
        '骨架卡': {
            '版本': '2.0（规则型）',
            '总字数': total_chars,
            '段落数': len(paragraphs),
            '句子数': len(sentences),
            # v5.0：写法规则（取代复制型段落结构）
            '写法规则': {
                '开头': '待 LLM 判断（如：环境描写制造压抑感 / 对话切入制造悬念）',
                '中段': '待 LLM 判断（如：冲突升级→转折→再升级）',
                '结尾': '待 LLM 判断（如：开放式结尾 / 总结式结尾 / 戛然而止）',
                '视角': '待 LLM 判断（第一/第三人称，全知/限知）',
                '对话风格': '待 LLM 判断（书面/口语，简洁/唠叨）',
                '描写偏好': '待 LLM 判断（视觉/听觉/嗅觉主导）',
            },
            # v5.0：结构变异许可
            '结构变异许可': {
                '允许插入闲笔': True,
                '允许打乱事件顺序': '部分允许（非核心事件）',
                '允许省略过程': True,
                '允许戛然而止': True,
                '允许视角微调': '第三人称中插入叙述者主观判断',
            },
            # v5.0：节奏要求（反检测）
            '节奏要求': {
                '段落长度方差比': f'最长/最短 >= 3.0（当前: {current_ratio}）',
                '超短句数量': f'>= {max(3, len(paragraphs))} 个（1-3字）当前: {micro_count}',
                '超长句数量': f'>= {max(2, len(paragraphs) // 2)} 个（50字+）当前: {mega_count}',
                '短句占比': '>= 40%',
                '长短句交替率': '>= 60%',
            },
            # v5.0：反检测约束
            '反检测约束': {
                '禁止使用': ['然而', '此外', '因此', '与此同时', '最后'],
                '对话要求': '必须包含打断、沉默、答非所问',
                '闲笔密度': '每2000字至少1处',
                '视角跳切': '至少1处叙述者主观判断',
            },
            # 参考结构（不强制遵循）
            '参考结构': [
                {
                    '段落': i,
                    '字数': count_chinese_chars(p),
                    '功能': '待 LLM 判断（仅参考，生成时可调整）',
                    '情绪': '待 LLM 判断'
                }
                for i, p in enumerate(paragraphs, 1)
            ],
            '节奏': {
                '句长分布': rhythm['sentence_length_distribution'],
                '平均句长': rhythm['mean_sentence_length'],
                '句长标准差': rhythm['std_sentence_length'],
                '突发性': rhythm['burstiness'],
                '段落长度分布': rhythm['paragraph_length_distribution']
            },
            '视角': {
                '人称': '待 LLM 判断',
                '聚焦': '待 LLM 判断',
                '范围': '待 LLM 判断'
            },
            '语言': {
                '句式偏好': '待 LLM 判断',
                '修辞密度': '待 LLM 判断',
                '对话比例': language['dialogue_ratio'],
                '叙述比例': language['narration_ratio'],
                '特殊标点': language['special_punctuation'],
                '的密度': language['de_density']
            },
            '情绪曲线': '待 LLM 标注'
        }
    }

    return skeleton


def main():
    if len(sys.argv) < 2:
        print("用法: python skeleton_extractor.py <原文文件.md> [输出文件.yaml]")
        sys.exit(1)

    input_file = Path(sys.argv[1])
    output_file = Path(sys.argv[2]) if len(sys.argv) > 2 else input_file.with_suffix('.skeleton.yaml')

    text = read_text_safe(input_file)
    if text.startswith('---'):
        parts = text.split('---', 2)
        if len(parts) >= 3:
            text = parts[2]

    skeleton = create_skeleton_card(text)

    # 输出为 YAML 格式（字符串拼接）
    yaml_lines = []
    yaml_lines.append('骨架卡:')
    for key, value in skeleton['骨架卡'].items():
        yaml_lines.append(f'  {key}: {value}')

    output_file.write_text('\n'.join(yaml_lines), encoding='utf-8')
    print(f"规则型骨架卡生成：{output_file}")
    print(f"请使用 LLM 参考 prompts/p01-skeleton-extract.md 完善此骨架卡")


if __name__ == '__main__':
    main()
