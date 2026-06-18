"""
anti_detection_checker.py
反检测验证工具（v3.0）
新增：段落方差、连接词多样性、信息密度波动、对话碎片化、闲笔密度、视角跳切

历史：
- v2.0：分级黑名单、上下文提取、合理阈值、段落级突发性
- v3.0：v5.0 升级，新增6项人类化检测指标
"""

import re
import json
import sys
import math
from pathlib import Path
import statistics


AI_WORDS_HARD_CN = [
    '综上所述', '总而言之', '归根结底',
    '不可否认的是', '值得注意的是', '令人深思的是',
    '这不禁让人想到', '留给我们的启示是',
    '深刻地揭示了', '从某种意义上说', '从另一个角度来看',
    '进行了一个', '开展了一项',
    '产生了一种', '形成了一种', '体现了一种',
    '表达了一种', '展现了一种',
    '不可或缺', '至关重要', '举足轻重',
    '众所周知', '不言而喻', '毋庸置疑',
    '与此同时也', '与此同时', '在…的背景下',
    '引发了广泛的', '受到了广泛的', '引起了广泛的',
    '发挥着重要的作用', '做出了巨大的贡献',
]

AI_WORDS_SOFT_CN = [
    '首先', '其次', '再次',
    '不仅', '而且',
    '一方面', '另一方面',
    '之所以', '是因为',
]

AI_WORDS_EN = [
    'furthermore', 'moreover', 'additionally', 'consequently',
    'therefore', 'thus', 'hence', 'nonetheless', 'nevertheless',
    'in addition', 'as a result', 'for instance', 'for example',
    'delve', 'explore', 'navigate', 'unravel', 'dissect',
    'tapestry', 'mosaic', 'intricate', 'nuanced', 'multifaceted',
    'in conclusion', 'to summarize', 'to conclude',
    'pivotal', 'crucial', 'essential', 'paramount',
]

PATTERNS_HARD = [
    (r'^首先.*\n其次.*\n最后', '三段式逻辑'),
    (r'^第一、.*\n第二、.*\n第三、', '三段式列举'),
    (r'^第一，.*\n第二，.*\n第三，', '三段式列举'),
    (r'综上所述[，。；]', '总结式结尾'),
    (r'总而言之[，。；]', '总结式结尾'),
]

PATTERNS_SOFT = [
    (r'因为.*所以', '因果结构'),
    (r'虽然.*但是', '转折结构'),
    (r'不仅.*而且', '递进结构'),
    (r'如果.*那么', '条件结构'),
    (r'一方面.*另一方面', '对照结构'),
    (r'之所以.*是因为', '因果结构'),
]


def count_chinese_chars(text):
    return len(re.findall(r'[\u4e00-\u9fff]', text))


def split_sentences(text):
    sentences = re.split(r'[。！？…]+', text)
    return [s.strip() for s in sentences if s.strip()]


def compute_burstiness(text):
    """计算全局突发性（句长标准差/均值）"""
    sentences = split_sentences(text)
    lengths = [count_chinese_chars(s) for s in sentences]
    if len(lengths) < 2:
        return {'global': 0, 'paragraphs': []}
    mean = statistics.mean(lengths)
    std = statistics.stdev(lengths)
    global_burstiness = round(std / mean, 4) if mean > 0 else 0

    paragraphs = re.split(r'\n\s*\n', text)
    paragraphs = [p.strip() for p in paragraphs if p.strip()]

    para_burstiness = []
    for i, p in enumerate(paragraphs, 1):
        p_sents = split_sentences(p)
        p_lengths = [count_chinese_chars(s) for s in p_sents]
        if len(p_lengths) >= 3:
            p_mean = statistics.mean(p_lengths)
            p_std = statistics.stdev(p_lengths)
            p_burst = round(p_std / p_mean, 4) if p_mean > 0 else 0
            para_burstiness.append({
                'paragraph': i,
                'burstiness': p_burst,
                'short_ratio': sum(1 for l in p_lengths if l <= 10) / len(p_lengths),
                'sentences': len(p_lengths),
                'mean_length': round(p_mean, 1),
                'std_length': round(p_std, 1)
            })

    return {
        'global': global_burstiness,
        'paragraphs': para_burstiness
    }


def compute_sentence_rhythm(text):
    """计算句子节奏指标"""
    sentences = split_sentences(text)
    lengths = [count_chinese_chars(s) for s in sentences]

    if not lengths:
        return {'short_ratio': 0, 'long_ratio': 0, 'alternation_rate': 0}

    short_count = sum(1 for l in lengths if l <= 10)
    long_count = sum(1 for l in lengths if l >= 25)
    total = len(lengths)

    alternations = 0
    for i in range(1, len(lengths)):
        if abs(lengths[i] - lengths[i-1]) >= 8:
            alternations += 1

    alternation_rate = alternations / (len(lengths) - 1) if len(lengths) > 1 else 0

    return {
        'short_ratio': round(short_count / total, 4) if total > 0 else 0,
        'long_ratio': round(long_count / total, 4) if total > 0 else 0,
        'alternation_rate': round(alternation_rate, 4),
        'total_sentences': total,
        'mean_length': round(statistics.mean(lengths), 1) if lengths else 0,
        'std_length': round(statistics.stdev(lengths), 1) if len(lengths) > 1 else 0,
        'lengths': lengths
    }


def compute_perplexity_simplified(text):
    chars = re.findall(r'[\u4e00-\u9fff]', text)
    if not chars:
        return 0

    freq = {}
    for c in chars:
        freq[c] = freq.get(c, 0) + 1

    total = len(chars)
    entropy = 0
    for count in freq.values():
        p = count / total
        if p > 0:
            entropy -= p * math.log2(p)

    perplexity = round(2 ** entropy * 5, 2)
    return perplexity


def scan_ai_words(text):
    """扫描AI特征词，分硬黑名单和软黑名单"""
    hard_hits = []
    for word in AI_WORDS_HARD_CN:
        positions = [m.start() for m in re.finditer(re.escape(word), text)]
        for pos in positions:
            context_start = max(0, pos - 15)
            context_end = min(len(text), pos + len(word) + 15)
            hard_hits.append({
                'word': word,
                'language': 'cn',
                'position': pos,
                'context': text[context_start:context_end],
                'severity': 'hard'
            })
    for word in AI_WORDS_EN:
        pattern = re.compile(r'\b' + re.escape(word) + r'\b', re.IGNORECASE)
        for m in pattern.finditer(text):
            context_start = max(0, m.start() - 15)
            context_end = min(len(text), m.end() + 15)
            hard_hits.append({
                'word': word,
                'language': 'en',
                'position': m.start(),
                'context': text[context_start:context_end],
                'severity': 'hard'
            })

    soft_hits = []
    for word in AI_WORDS_SOFT_CN:
        count = text.count(word)
        if count > 0:
            pos = text.find(word)
            context_start = max(0, pos - 15)
            context_end = min(len(text), pos + len(word) + 15)
            soft_hits.append({
                'word': word,
                'language': 'cn',
                'count': count,
                'first_position': pos,
                'context': text[context_start:context_end],
                'severity': 'soft'
            })

    return hard_hits, soft_hits


# ============ v5.0 新增检测函数 ============

def split_paragraphs(text):
    """按空行分段"""
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


def check_paragraph_variance(text):
    """检测段落长度方差比（最长/最短）"""
    paragraphs = split_paragraphs(text)
    if len(paragraphs) < 2:
        return {'ratio': 1.0, 'pass': False, 'note': '段落数不足'}
    
    lengths = [count_chinese_chars(p) for p in paragraphs]
    max_len = max(lengths)
    min_len = min(l for l in lengths if l > 0)
    ratio = max_len / min_len if min_len > 0 else 1.0
    
    return {
        'ratio': round(ratio, 2),
        'max_len': max_len,
        'min_len': min_len,
        'paragraph_count': len(paragraphs),
        'target': '≥ 3.0',
        'pass': ratio >= 3.0
    }


def check_connector_diversity(text):
    """检测连接词多样性（同义替换率）"""
    connector_groups = {
        '转折': ['然而', '但是', '不过', '可', '但', '只是', '倒也是'],
        '递进': ['此外', '而且', '并且', '再说', '还有', '另外'],
        '因果': ['因此', '所以', '于是', '因而', '结果', '就这么着'],
        '并列': ['同时', '与此同时', '一边', '一边…一边', '那会儿'],
        '总结': ['最后', '总之', '归根结底', '说到底', '临了', '末了'],
    }
    
    total_connectors = 0
    diversified = 0
    group_counts = {}
    
    for group_name, words in connector_groups.items():
        counts = {}
        for word in words:
            c = text.count(word)
            if c > 0:
                counts[word] = c
        
        if counts:
            total_connectors += sum(counts.values())
            group_counts[group_name] = counts
            # 如果使用了2种以上不同的连接词，视为多样化
            if len(counts) >= 2:
                diversified += sum(counts.values())
    
    diversity_rate = diversified / total_connectors if total_connectors > 0 else 0
    
    return {
        'diversity_rate': round(diversity_rate, 4),
        'total_connectors': total_connectors,
        'group_counts': group_counts,
        'target': '≥ 0.6',
        'pass': diversity_rate >= 0.6 or total_connectors == 0
    }


def check_density_fluctuation(text):
    """检测相邻段落信息密度波动"""
    paragraphs = split_paragraphs(text)
    if len(paragraphs) < 2:
        return {'fluctuation_rate': 0, 'pass': False, 'note': '段落数不足'}
    
    lengths = [count_chinese_chars(p) for p in paragraphs]
    fluctuations = []
    
    for i in range(1, len(lengths)):
        diff = abs(lengths[i] - lengths[i-1])
        avg = (lengths[i] + lengths[i-1]) / 2
        fluctuation = diff / avg if avg > 0 else 0
        fluctuations.append(fluctuation)
    
    avg_fluctuation = statistics.mean(fluctuations) if fluctuations else 0
    
    return {
        'fluctuation_rate': round(avg_fluctuation, 4),
        'pair_count': len(fluctuations),
        'target': '≥ 0.5',
        'pass': avg_fluctuation >= 0.5
    }


def check_dialogue_fragmentation(text):
    """检测对话碎片化率"""
    # 匹配所有对话
    dialogues = re.findall(r'"([^"]{3,100})"', text)
    if not dialogues:
        return {'fragmentation_rate': 0, 'pass': False, 'note': '未检测到对话'}
    
    # 检测碎片化特征
    fragmented = 0
    for d in dialogues:
        # 打断特征
        if '——' in d or d.endswith('—'):
            fragmented += 1
            continue
        # 省略特征
        if '……' in d or d.startswith('…'):
            fragmented += 1
            continue
        # 重复特征
        if re.search(r'(.)\、\1', d):
            fragmented += 1
            continue
        # 口吃特征
        if re.search(r'([\u4e00-\u9fff])\、\1', d):
            fragmented += 1
            continue
        # 反问特征
        if d.endswith('？') and len(d) < 10:
            fragmented += 1
            continue
        # 极短对话（沉默/动作代替）
        if len(d) <= 4:
            fragmented += 1
            continue
        # 答非所问特征（包含常见不匹配模式）
        if '天挺热的' in d or '你说呢' in d or '算了' in d:
            fragmented += 1
            continue
    
    rate = fragmented / len(dialogues)
    
    return {
        'fragmentation_rate': round(rate, 4),
        'fragmented_count': fragmented,
        'total_dialogues': len(dialogues),
        'target': '≥ 0.3',
        'pass': rate >= 0.3
    }


def check_digression_density(text):
    """检测闲笔密度（与主线无关的感官细节）"""
    # 使用启发式规则检测闲笔：包含特定感官词且不在引号内的独立句子
    digression_markers = ['记得', '想起', '那年', '小时候', '外婆', '父亲', '母亲',
                          '味道', '气味', '香味', '臭味', '声音', '传来',
                          '窗外', '墙角', '窗台', '远处', '落叶', '阳光']
    
    sentences = split_sentences(text)
    digression_count = 0
    
    for sent in sentences:
        # 排除对话内的句子
        if '"' in sent:
            continue
        # 检测是否包含闲笔标记
        if any(marker in sent for marker in digression_markers):
            # 进一步检查：是否包含具体感官细节
            if re.search(r'[\u4e00-\u9fff]{2,}的[\u4e00-\u9fff]{2,}', sent):
                digression_count += 1
    
    total_chars = count_chinese_chars(text)
    density = digression_count / (total_chars / 1000) if total_chars > 0 else 0
    
    return {
        'digression_count': digression_count,
        'density_per_1000': round(density, 4),
        'target': '≥ 0.5 处/千字',
        'pass': density >= 0.5
    }


def check_perspective_jump(text):
    """检测视角跳切次数"""
    # 检测第三人称叙述中突然插入的主观判断
    jump_markers = [
        r'说来也怪',
        r'那年头',
        r'话说回来',
        r'平心而论',
        r'说实在的',
        r'讲真',
        r'不得不说',
        r'仔细想来',
        r'如今想想',
    ]
    
    jumps = 0
    for marker in jump_markers:
        jumps += len(re.findall(marker, text))
    
    # 也检测叙述者的直接评论（"你"在第三人称中的突兀使用）
    narrator_intrusions = len(re.findall(r'[^"]?你能想象', text))
    jumps += narrator_intrusions
    
    return {
        'jump_count': jumps,
        'target': '≥ 1',
        'pass': jumps >= 1
    }


# ============ 修改后的 check 函数 ============


def scan_patterns(text):
    """扫描模式化标记，分硬模式和软模式"""
    hard_hits = []
    for pattern_desc in PATTERNS_HARD:
        pattern = pattern_desc[0]
        label = pattern_desc[1]
        match = re.search(pattern, text, re.DOTALL)
        if match:
            start = match.start()
            context_start = max(0, start - 20)
            context_end = min(len(text), match.end() + 20)
            hard_hits.append({
                'pattern': pattern,
                'label': label,
                'matched_text': match.group(),
                'position': start,
                'context': text[context_start:context_end],
                'severity': 'hard'
            })

    soft_hits = []
    for pattern_desc in PATTERNS_SOFT:
        pattern = pattern_desc[0]
        label = pattern_desc[1]
        matches = list(re.finditer(pattern, text, re.DOTALL))
        for m in matches:
            start = m.start()
            context_start = max(0, start - 20)
            context_end = min(len(text), m.end() + 20)
            soft_hits.append({
                'pattern': pattern,
                'label': label,
                'matched_text': m.group(),
                'position': start,
                'context': text[context_start:context_end],
                'severity': 'soft'
            })

    return hard_hits, soft_hits


def check(text, has_local_model=False):
    """执行反检测检查（v3.0）"""
    burstiness_result = compute_burstiness(text)
    rhythm = compute_sentence_rhythm(text)

    hard_ai_hits, soft_ai_hits = scan_ai_words(text)
    hard_pattern_hits, soft_pattern_hits = scan_patterns(text)

    total_soft_ai = sum(h['count'] for h in soft_ai_hits)
    total_soft_patterns = len(soft_pattern_hits)

    # v5.0 新增检测
    para_variance = check_paragraph_variance(text)
    connector_div = check_connector_diversity(text)
    density_fluc = check_density_fluctuation(text)
    dialogue_frag = check_dialogue_fragmentation(text)
    digression = check_digression_density(text)
    perspective = check_perspective_jump(text)

    # 通过判断
    hard_pass = len(hard_ai_hits) == 0 and len(hard_pattern_hits) == 0
    soft_pass = total_soft_ai <= 5 and total_soft_patterns <= 3
    burstiness_pass = burstiness_result['global'] > 0.7
    rhythm_pass = rhythm['short_ratio'] >= 0.15 and rhythm['alternation_rate'] >= 0.10
    
    # v5.0 新增通过条件
    variance_pass = para_variance['pass']
    connector_pass = connector_div['pass']
    density_pass = density_fluc['pass']
    dialogue_pass = dialogue_frag['pass']
    digression_pass = digression['pass']
    perspective_pass = perspective['pass']

    overall_pass = (hard_pass and soft_pass and burstiness_pass and rhythm_pass and
                   variance_pass and connector_pass and density_pass and
                   dialogue_pass and digression_pass and perspective_pass)

    result = {
        'version': '3.0',
        'perplexity': {
            'value': compute_perplexity_simplified(text),
            'target': '> 80',
            'note': '简化计算，仅供参考。建议使用本地语言模型或外部工具获取准确困惑度。'
        },
        'burstiness': {
            'value': burstiness_result['global'],
            'target': '> 0.7',
            'pass': burstiness_pass,
            'paragraphs': burstiness_result['paragraphs']
        },
        'sentence_rhythm': rhythm,
        'ai_words': {
            'hard': {
                'count': len(hard_ai_hits),
                'hits': hard_ai_hits,
                'target': '0',
                'pass': len(hard_ai_hits) == 0
            },
            'soft': {
                'count': total_soft_ai,
                'hits': soft_hits_to_summary(soft_ai_hits),
                'target': '≤ 5',
                'pass': total_soft_ai <= 5,
                'note': '软黑名单词在日常中文中常见，允许少量使用'
            }
        },
        'patterns': {
            'hard': {
                'count': len(hard_pattern_hits),
                'hits': hard_pattern_hits,
                'target': '0',
                'pass': len(hard_pattern_hits) == 0
            },
            'soft': {
                'count': total_soft_patterns,
                'hits': soft_pattern_hits,
                'target': '≤ 3',
                'pass': total_soft_patterns <= 3,
                'note': '常见转折/因果/条件结构在日常写作中偶尔出现，允许少量'
            }
        },
        # v5.0 新增指标
        'paragraph_variance': para_variance,
        'connector_diversity': connector_div,
        'density_fluctuation': density_fluc,
        'dialogue_fragmentation': dialogue_frag,
        'digression_density': digression,
        'perspective_jump': perspective,
        'pass': overall_pass,
        'criteria': {
            'hard_ai_words': '0',
            'soft_ai_words': '≤ 5',
            'hard_patterns': '0',
            'soft_patterns': '≤ 3',
            'burstiness': '> 0.7',
            'short_ratio': '≥ 0.15',
            'alternation_rate': '≥ 0.10',
            'paragraph_variance_ratio': '≥ 3.0',
            'connector_diversity': '≥ 0.6',
            'density_fluctuation': '≥ 0.5',
            'dialogue_fragmentation': '≥ 0.3',
            'digression_density': '≥ 0.5/千字',
            'perspective_jump': '≥ 1'
        }
    }
    
    return result


def soft_hits_to_summary(soft_hits):
    """简化软黑名单输出"""
    return [{'word': h['word'], 'count': h['count'], 'severity': 'soft'} for h in soft_hits]


def main():
    if len(sys.argv) < 2:
        print("用法: python anti_detection_checker.py <新篇文件.md> [输出报告.json]")
        print("说明：困惑度计算为简化版，建议使用本地模型或外部工具验证")
        sys.exit(1)

    input_file = Path(sys.argv[1])
    output_file = Path(sys.argv[2]) if len(sys.argv) > 2 else input_file.with_suffix('.anti_detection.json')

    text = input_file.read_text(encoding='utf-8')
    if text.startswith('---'):
        parts = text.split('---', 2)
        if len(parts) >= 3:
            text = parts[2]

    result = check(text)

    output_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"反检测检查完成：{output_file}")
    print(f"突发性：{result['burstiness']['value']} / 目标 > 0.7 / {'通过' if result['burstiness']['pass'] else '未通过'}")
    print(f"短句占比：{result['sentence_rhythm']['short_ratio']:.2%} / 目标 ≥ 15%")
    print(f"长短句交替率：{result['sentence_rhythm']['alternation_rate']:.2%} / 目标 ≥ 10%")
    print(f"硬黑名单 AI 特征词：{result['ai_words']['hard']['count']} 个 / 目标 0 / {'通过' if result['ai_words']['hard']['pass'] else '未通过'}")
    print(f"软黑名单 AI 特征词：{result['ai_words']['soft']['count']} 次 / 目标 ≤ 5 / {'通过' if result['ai_words']['soft']['pass'] else '未通过'}")
    print(f"硬模式化标记：{result['patterns']['hard']['count']} 个 / 目标 0 / {'通过' if result['patterns']['hard']['pass'] else '未通过'}")
    print(f"软模式化标记：{result['patterns']['soft']['count']} 个 / 目标 ≤ 3 / {'通过' if result['patterns']['soft']['pass'] else '未通过'}")
    # v5.0 新增输出
    print(f"段落长度方差比：{result['paragraph_variance']['ratio']} / 目标 ≥ 3.0 / {'通过' if result['paragraph_variance']['pass'] else '未通过'}")
    print(f"连接词多样性：{result['connector_diversity']['diversity_rate']:.2%} / 目标 ≥ 0.6 / {'通过' if result['connector_diversity']['pass'] else '未通过'}")
    print(f"信息密度波动：{result['density_fluctuation']['fluctuation_rate']:.2%} / 目标 ≥ 0.5 / {'通过' if result['density_fluctuation']['pass'] else '未通过'}")
    print(f"对话碎片化率：{result['dialogue_fragmentation']['fragmentation_rate']:.2%} / 目标 ≥ 0.3 / {'通过' if result['dialogue_fragmentation']['pass'] else '未通过'}")
    print(f"闲笔密度：{result['digression_density']['density_per_1000']:.2f} 处/千字 / 目标 ≥ 0.5 / {'通过' if result['digression_density']['pass'] else '未通过'}")
    print(f"视角跳切：{result['perspective_jump']['jump_count']} 次 / 目标 ≥ 1 / {'通过' if result['perspective_jump']['pass'] else '未通过'}")
    print(f"最终结果：{'通过' if result['pass'] else '未通过'}")


if __name__ == '__main__':
    main()