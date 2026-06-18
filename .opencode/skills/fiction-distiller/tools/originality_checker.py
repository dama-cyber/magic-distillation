"""
originality_checker.py
原创性验证工具（v2.0）
检测N-gram重合、变量残留、最长公共子串、同义替换禁忌
新增：骨架相似度、情绪曲线差异、信息密度分布差异
改进：分级残留检测、段落级分析、LCS定位、上下文提取
"""

import re
import json
import sys
import math
from pathlib import Path
from collections import defaultdict
from encoding_utils import read_text_safe


def count_chinese_chars(text):
    return len(re.findall(r'[\u4e00-\u9fff]', text))


def clean_text(text):
    if text.startswith('---'):
        parts = text.split('---', 2)
        if len(parts) >= 3:
            text = parts[2]
    text = re.sub(r'[^\u4e00-\u9fffa-zA-Z0-9]', '', text)
    return text


def get_ngrams(text, n):
    return [text[i:i+n] for i in range(len(text) - n + 1)]


def ngram_overlap(original, new, n):
    orig_ngrams = set(get_ngrams(original, n))
    new_ngrams = get_ngrams(new, n)
    if not new_ngrams:
        return 0, 0, [], []
    overlap = [ng for ng in new_ngrams if ng in orig_ngrams]
    overlap_set = set(overlap)
    overlap_positions = [(new.find(ng), ng) for ng in overlap_set if new.find(ng) >= 0]
    return len(overlap_set), len(overlap_set) / len(set(new_ngrams)) if set(new_ngrams) else 0, overlap_set, overlap_positions


def longest_common_substring(s1, s2):
    if not s1 or not s2:
        return '', 0, -1, -1

    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    max_len = 0
    end_pos_1 = 0
    end_pos_2 = 0

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i-1] == s2[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
                if dp[i][j] > max_len:
                    max_len = dp[i][j]
                    end_pos_1 = i
                    end_pos_2 = j

    lcs = s1[end_pos_1 - max_len:end_pos_1]

    orig_context_start = max(0, end_pos_1 - max_len - 20)
    orig_context_end = min(len(s1), end_pos_1 + 20)
    new_context_start = max(0, end_pos_2 - max_len - 20)
    new_context_end = min(len(s2), end_pos_2 + 20)

    return lcs, max_len, end_pos_1, end_pos_2


COMMON_PHRASES_4 = {
    '不知道为什么', '看了看四周', '走了过去', '说了一句话', '不知道该说',
    '不知道自己', '不知道他是', '忍不住想', '忍不住笑', '忍不住哭',
    '忍不住问', '不由自主', '不知道从', '不知道这', '没有说话',
    '不知道在', '看了一眼', '看不出来', '想了想', '不知道啊',
    '怎么说呢', '怎么会呢', '这也太', '大家都知道', '不知道谁',
    '不能不说', '不得不承认', '不知道怎么', '说不出话',
    '是不是', '想知道', '不知道了', '打招呼', '说不出',
    '是不是有', '看不出来', '不一样了', '不由得想',
    '不知道为', '忍不住地', '没有什么', '就这样吧',
}

COMMON_PHRASES_6_PLUS = {
    '已经不知道该说什么', '不知道该怎么说', '忍不住想要知道',
    '不由自主地想', '看了又看', '说也不是不说也不是',
    '不知道为什么就', '什么都没有说', '什么都不知道',
    '已经没有办法', '再也没有回头', '再也不想回去',
    '已经不再是从前', '不知道是不是', '能不一样吗',
    '没有什么比这更', '已经过去了', '没有什么能比',
    '你不知道我一个人', '你不知道在外面',
}


def is_common_phrase(fragment):
    if len(fragment) <= 3:
        return True
    if fragment in COMMON_PHRASES_4:
        return True
    if fragment in COMMON_PHRASES_6_PLUS:
        return True
    common_single = '的了是在有过和与被把而却都也能就让已还又着呢吗吧啊哦嗯呀么'
    if all(c in common_single for c in fragment):
        return True
    return False


def scan_variables(original_text, new_text, variables):
    """扫描变量残留，分级检测"""
    real_residues = []
    potential_residues_7plus = []
    potential_residues_4_6 = []

    if variables:
        for var in variables:
            original = var.get('original', '')
            new_design = var.get('new', '')
            if original and len(original) >= 2 and original in new_text:
                real_residues.append({
                    'type': '真实变量残留',
                    'category': var.get('type', '未知'),
                    'original': original,
                    'position': new_text.find(original),
                    'context': new_text[max(0, new_text.find(original)-10):new_text.find(original)+len(original)+10],
                    'severity': 'high'
                })

    orig_clean = clean_text(original_text)
    new_clean = clean_text(new_text)

    for i in range(0, len(orig_clean) - 6):
        fragment = orig_clean[i:i+7]
        if len(fragment) >= 7 and fragment in new_clean:
            if not is_common_phrase(fragment):
                pos = new_clean.find(fragment)
                potential_residues_7plus.append({
                    'type': '潜在残留(7字+)',
                    'original': fragment,
                    'position': pos,
                    'context': new_clean[max(0, pos-10):pos+len(fragment)+10],
                    'severity': 'medium'
                })

    for i in range(0, len(orig_clean) - 3):
        fragment = orig_clean[i:i+4]
        if len(fragment) >= 4 and fragment in new_clean and len(fragment) < 7:
            if not is_common_phrase(fragment):
                pos = new_clean.find(fragment)
                if not any(r['original'] == fragment for r in potential_residues_7plus):
                    if not any(r['original'] == fragment for r in potential_residues_4_6):
                        pos_count = new_clean.count(fragment)
                        if pos_count <= 3:
                            potential_residues_4_6.append({
                                'type': '日常短语残留(4-6字)',
                                'original': fragment,
                                'position': pos,
                                'context': new_clean[max(0, pos-10):pos+len(fragment)+10],
                                'count': pos_count,
                                'severity': 'low'
                            })

    potential_residues_4_6.sort(key=lambda x: x.get('count', 0))

    return real_residues, potential_residues_7plus, potential_residues_4_6


def paragraph_level_overlap(original_text, new_text, n=5):
    """计算段落级原创性分析"""
    orig_paragraphs = [p.strip() for p in re.split(r'\n\s*\n', original_text) if p.strip()]
    new_paragraphs = [p.strip() for p in re.split(r'\n\s*\n', new_text) if p.strip()]

    results = []
    max_check = min(len(orig_paragraphs), len(new_paragraphs))

    for i in range(max_check):
        orig_clean = clean_text(orig_paragraphs[i])
        new_clean_p = clean_text(new_paragraphs[i])

        if not orig_clean or not new_clean_p:
            results.append({
                'paragraph': i + 1,
                'ngram_overlap': 0,
                'lcs_length': 0,
                'status': 'ok'
            })
            continue

        overlap_count, overlap_ratio, _, _ = ngram_overlap(orig_clean, new_clean_p, n)
        lcs, lcs_len, _, _ = longest_common_substring(orig_clean, new_clean_p)

        status = 'ok'
        if overlap_ratio > 0.1 or lcs_len > 15:
            status = 'high_overlap'
        elif overlap_ratio > 0.05 or lcs_len > 8:
            status = 'medium_overlap'

        results.append({
            'paragraph': i + 1,
            'ngram_overlap': round(overlap_ratio, 4),
            'lcs_length': lcs_len,
            'lcs_preview': lcs[:30] if lcs else '',
            'status': status
        })

    return results


def sentence_similarity(original, new):
    """计算句子结构相似度（改进版：考虑句长分布和句式模式）"""
    orig_sentences = re.split(r'[。！？…]+', original)
    new_sentences = re.split(r'[。！？…]+', new)
    orig_sentences = [s.strip() for s in orig_sentences if s.strip()]
    new_sentences = [s.strip() for s in new_sentences if s.strip()]

    if not orig_sentences or not new_sentences:
        return {'score': 0, 'method': 'insufficient_data', 'details': []}

    orig_lengths = [count_chinese_chars(s) for s in orig_sentences]
    new_lengths = [count_chinese_chars(s) for s in new_sentences]

    length_corr = 0
    min_len = min(len(orig_lengths), len(new_lengths))
    if min_len > 0:
        orig_segment = orig_lengths[:min_len]
        new_segment = new_lengths[:min_len]
        mean_orig = sum(orig_segment) / len(orig_segment) if orig_segment else 1
        mean_new = sum(new_segment) / len(new_segment) if new_segment else 1
        std_orig = (sum((x - mean_orig) ** 2 for x in orig_segment) / len(orig_segment)) ** 0.5 if orig_segment else 1
        std_new = (sum((x - mean_new) ** 2 for x in new_segment) / len(new_segment)) ** 0.5 if new_segment else 1

        if min_len >= 3:
            norm_orig = [(x - mean_orig) / std_orig if std_orig > 0 else 0 for x in orig_segment]
            norm_new = [(x - mean_new) / std_new if std_new > 0 else 0 for x in new_segment]
            corr_sum = sum(a * b for a, b in zip(norm_orig, norm_new))
            length_corr = corr_sum / min_len if min_len > 0 else 0

    structural_matches = 0
    for i in range(min_len):
        if abs(orig_lengths[i] - new_lengths[i]) <= 3:
            if orig_lengths[i] > 10:
                structural_matches += 1

    structural_corr = structural_matches / min_len if min_len > 0 else 0

    overall = round(max(0, min(1, length_corr * 0.5 + structural_corr * 0.5)), 4)

    return {
        'score': overall,
        'length_correlation': round(corr_sum / min_len, 4) if min_len > 0 else 0,
        'structural_match_ratio': round(structural_corr, 4),
        'total_compared': min_len,
        'method': 'improved_correlation'
    }


def check(original_file, new_file, variable_file=None, taboo_file=None):
    original_text = read_text_safe(original_file)
    new_text = read_text_safe(new_file)

    orig_clean = clean_text(original_text)
    new_clean = clean_text(new_text)

    variables = None
    if variable_file and variable_file.exists():
        try:
            var_data = json.loads(variable_file.read_text(encoding='utf-8'))
            if isinstance(var_data, dict):
                variables = var_data.get('variables', [])
            elif isinstance(var_data, list):
                variables = var_data
        except json.JSONDecodeError:
            variables = None

    taboo_words = []
    if taboo_file and taboo_file.exists():
        try:
            taboo_data = json.loads(taboo_file.read_text(encoding='utf-8'))
            taboo_words = taboo_data if isinstance(taboo_data, list) else taboo_data.get('taboo_words', [])
        except json.JSONDecodeError:
            taboo_words = []

    ngram_results = {}
    for n in [3, 5, 8, 12]:
        count, ratio, overlap_set, positions = ngram_overlap(orig_clean, new_clean, n)
        ngram_results[f'{n}-gram'] = {
            'overlap_count': count,
            'overlap_ratio': round(ratio, 4),
            'examples': list(overlap_set)[:20],
            'categories': categorize_ngrams(overlap_set, n)
        }

    lcs, lcs_len, lcs_pos_orig, lcs_pos_new = longest_common_substring(orig_clean, new_clean)

    real_residues, potential_7plus, potential_4_6 = scan_variables(original_text, new_text, variables)

    taboo_hits = []
    if taboo_words:
        for word in taboo_words:
            if word in new_text:
                taboo_hits.append({
                    'word': word,
                    'position': new_text.find(word),
                    'context': new_text[max(0, new_text.find(word)-10):new_text.find(word)+len(word)+10]
                })

    struct_sim = sentence_similarity(original_text, new_text)

    para_overlap = paragraph_level_overlap(original_text, new_text)

    high_overlap_paras = [p for p in para_overlap if p['status'] != 'ok']

    # v5.0 新增检测
    skeleton_sim = check_skeleton_similarity(original_text, new_text)
    emotion_sim = check_emotion_curve_similarity(original_text, new_text)
    density_sim = check_density_distribution_similarity(original_text, new_text)

    pass_5gram = ngram_results['5-gram']['overlap_ratio'] < 0.05
    pass_8gram = ngram_results['8-gram']['overlap_count'] < 10
    pass_real_residue = len(real_residues) == 0
    pass_potential_7plus = len(potential_7plus) <= 5
    pass_lcs = lcs_len < 8
    pass_struct = struct_sim['score'] < 0.5
    pass_taboo = len(taboo_hits) == 0
    
    # v5.0 新增通过条件
    pass_skeleton = skeleton_sim['pass']
    pass_emotion = emotion_sim['pass']
    pass_density = density_sim['pass']

    return {
        'version': '2.0',
        'ngram_results': ngram_results,
        'longest_common_substring': {
            'content': lcs,
            'length': lcs_len,
            'position_in_original': lcs_pos_orig,
            'position_in_new': lcs_pos_new,
            'context_in_new': new_clean[max(0, lcs_pos_new-lcs_len-20):lcs_pos_new+20] if lcs else ''
        },
        'variable_residues': {
            'real_residues': real_residues,
            'potential_7plus': potential_7plus,
            'potential_4_6_count': len(potential_4_6),
            'potential_4_6_top10': potential_4_6[:10],
            'total_residues': len(real_residues) + len(potential_7plus),
            'details_note': 'potential_4_6 contains common Chinese phrases with high false positive rate, shown separately'
        },
        'taboo_hits': taboo_hits,
        'sentence_structure_similarity': struct_sim,
        'paragraph_overlap': para_overlap,
        'high_overlap_paragraphs': high_overlap_paras,
        # v5.0 新增
        'skeleton_similarity': skeleton_sim,
        'emotion_curve_similarity': emotion_sim,
        'density_distribution_similarity': density_sim,
        'pass': pass_5gram and pass_8gram and pass_real_residue and pass_potential_7plus and pass_lcs and pass_struct and pass_taboo and pass_skeleton and pass_emotion and pass_density,
        'criteria': {
            '5gram_ratio': '< 5%',
            '8gram_count': '< 10',
            'real_residue_count': '0',
            'potential_7plus_count': '≤ 5',
            'lcs_length': '< 8',
            'structure_similarity': '< 0.5',
            'taboo_hit_count': '0',
            'skeleton_similarity': '< 0.5',
            'emotion_curve_dtw': '足够大（情绪走势不同）',
            'density_correlation': '< 0.6'
        }
    }


def categorize_ngrams(overlap_set, n):
    """将 N-gram 重叠分类"""
    categories = {
        'common_phrases': 0,
        'unique_overlaps': 0,
        'examples': []
    }
    for ng in list(overlap_set)[:50]:
        if is_common_phrase(ng):
            categories['common_phrases'] += 1
        else:
            categories['unique_overlaps'] += 1
        if len(categories['examples']) < 5 and not is_common_phrase(ng):
            categories['examples'].append(ng)
    return categories


# ============ v5.0 新增：骨架/情绪/密度相似度检测 ============

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


def classify_paragraph_function(text):
    """粗略判断段落功能"""
    # 基于内容特征简单分类
    if re.search(r'^[\s]*[""""]', text):
        return 'dialogue'
    if len(text) < 50:
        return 'short_hook'
    if re.search(r'[。！？]{3,}', text):
        return 'climax'
    if re.search(r'[记][得]|小时[候候]', text):
        return 'flashback'
    if re.search(r'[看看][见到到]|听[见到到]|闻[到着]', text):
        return 'sensory'
    if re.search(r'[想][象到到]|觉[得]', text):
        return 'internal'
    return 'narrative'


def check_skeleton_similarity(original_text, new_text):
    """
    检测骨架相似度：段落功能序列的相似性
    如果新篇的段落功能分布与原文过于相似，视为骨架复制
    """
    orig_paras = split_paragraphs(original_text)
    new_paras = split_paragraphs(new_text)
    
    if len(orig_paras) < 2 or len(new_paras) < 2:
        return {'similarity': 0, 'pass': True, 'note': '段落数不足'}
    
    orig_funcs = [classify_paragraph_function(p) for p in orig_paras]
    new_funcs = [classify_paragraph_function(p) for p in new_paras]
    
    # 计算功能分布的相似度（使用余弦相似度）
    func_types = list(set(orig_funcs + new_funcs))
    orig_dist = [orig_funcs.count(f) / len(orig_funcs) for f in func_types]
    new_dist = [new_funcs.count(f) / len(new_funcs) for f in func_types]
    
    # 点积
    dot = sum(a * b for a, b in zip(orig_dist, new_dist))
    # 模长
    norm_orig = math.sqrt(sum(a * a for a in orig_dist))
    norm_new = math.sqrt(sum(b * b for b in new_dist))
    
    similarity = dot / (norm_orig * norm_new) if norm_orig > 0 and norm_new > 0 else 0
    
    return {
        'similarity': round(similarity, 4),
        'orig_functions': orig_funcs[:10],
        'new_functions': new_funcs[:10],
        'target': '< 0.5',
        'pass': similarity < 0.5
    }


def extract_emotion_curve(text, sample_points=10):
    """
    提取情绪曲线（简化版）
    基于标点、句式、词汇判断每个采样点的情绪强度
    """
    sentences = re.split(r'[。！？…]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if not sentences:
        return []
    
    # 情绪标记词
    high_emotion = ['死', '杀', '血', '哭', ' scream', '尖叫', '怒吼', '绝望', '疯狂']
    medium_emotion = ['紧张', '害怕', '担心', '焦虑', '兴奋', '激动', '惊讶']
    low_emotion = ['平静', '安静', '慢慢', '轻轻', '沉默', '发呆']
    
    curve = []
    for sent in sentences:
        score = 0.5  # 中性
        if any(w in sent for w in high_emotion):
            score = 1.0
        elif any(w in sent for w in medium_emotion):
            score = 0.75
        elif any(w in sent for w in low_emotion):
            score = 0.25
        
        # 标点加成
        if '！' in sent or '？' in sent:
            score += 0.1
        if '……' in sent:
            score -= 0.1
        
        curve.append(min(1.0, max(0.0, score)))
    
    # 采样到固定点数
    if len(curve) <= sample_points:
        return curve
    
    step = len(curve) / sample_points
    sampled = []
    for i in range(sample_points):
        idx = int(i * step)
        sampled.append(curve[min(idx, len(curve) - 1)])
    
    return sampled


def dtw_distance(seq1, seq2):
    """简化版动态时间规整距离"""
    n, m = len(seq1), len(seq2)
    if n == 0 or m == 0:
        return float('inf')
    
    # 使用欧氏距离
    dtw = [[float('inf')] * (m + 1) for _ in range(n + 1)]
    dtw[0][0] = 0
    
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = abs(seq1[i-1] - seq2[j-1])
            dtw[i][j] = cost + min(dtw[i-1][j], dtw[i][j-1], dtw[i-1][j-1])
    
    return dtw[n][m]


def check_emotion_curve_similarity(original_text, new_text):
    """检测情绪曲线相似度（DTW距离）"""
    orig_curve = extract_emotion_curve(original_text)
    new_curve = extract_emotion_curve(new_text)
    
    if not orig_curve or not new_curve:
        return {'dtw_distance': 0, 'pass': True, 'note': '无法提取情绪曲线'}
    
    distance = dtw_distance(orig_curve, new_curve)
    
    # 归一化：距离越小越相似
    max_possible = max(len(orig_curve), len(new_curve))
    normalized = distance / max_possible if max_possible > 0 else 0
    
    return {
        'dtw_distance': round(distance, 4),
        'normalized_distance': round(normalized, 4),
        'orig_curve': [round(x, 2) for x in orig_curve],
        'new_curve': [round(x, 2) for x in new_curve],
        'target': 'DTW 距离应足够大（情绪走势不同）',
        'pass': normalized > 0.3  # 阈值可调整
    }


def check_density_distribution_similarity(original_text, new_text):
    """
    检测信息密度分布相似度
    比较两文本的段落字数分布相关性
    """
    orig_paras = split_paragraphs(original_text)
    new_paras = split_paragraphs(new_text)
    
    if len(orig_paras) < 2 or len(new_paras) < 2:
        return {'correlation': 0, 'pass': True, 'note': '段落数不足'}
    
    orig_lengths = [count_chinese_chars(p) for p in orig_paras]
    new_lengths = [count_chinese_chars(p) for p in new_paras]
    
    # 如果长度不同，对较短的进行线性插值
    if len(orig_lengths) != len(new_lengths):
        target_len = max(len(orig_lengths), len(new_lengths))
        orig_lengths = interpolate_list(orig_lengths, target_len)
        new_lengths = interpolate_list(new_lengths, target_len)
    
    # 计算皮尔逊相关系数
    n = len(orig_lengths)
    mean_o = sum(orig_lengths) / n
    mean_n = sum(new_lengths) / n
    
    cov = sum((o - mean_o) * (nn - mean_n) for o, nn in zip(orig_lengths, new_lengths))
    std_o = math.sqrt(sum((o - mean_o) ** 2 for o in orig_lengths))
    std_n = math.sqrt(sum((nn - mean_n) ** 2 for nn in new_lengths))
    
    correlation = cov / (std_o * std_n) if std_o > 0 and std_n > 0 else 0
    
    return {
        'correlation': round(correlation, 4),
        'orig_distribution': orig_lengths[:10],
        'new_distribution': new_lengths[:10],
        'target': '< 0.6',
        'pass': abs(correlation) < 0.6
    }


def interpolate_list(data, target_len):
    """线性插值到目标长度"""
    if len(data) == target_len:
        return data
    if len(data) == 1:
        return data * target_len
    
    result = []
    step = (len(data) - 1) / (target_len - 1) if target_len > 1 else 0
    for i in range(target_len):
        idx = i * step
        low = int(idx)
        high = min(low + 1, len(data) - 1)
        frac = idx - low
        val = data[low] * (1 - frac) + data[high] * frac
        result.append(val)
    
    return result


# ============ 修改后的 check 函数 ============


def main():
    if len(sys.argv) < 3:
        print("用法: python originality_checker.py <原文文件.md> <新篇文件.md> [换元清单.json] [禁忌清单.json] [输出报告.json]")
        sys.exit(1)

    original_file = Path(sys.argv[1])
    new_file = Path(sys.argv[2])
    variable_file = Path(sys.argv[3]) if len(sys.argv) > 3 else None
    taboo_file = Path(sys.argv[4]) if len(sys.argv) > 4 else None
    output_file = Path(sys.argv[5]) if len(sys.argv) > 5 else new_file.with_suffix('.originality.json')

    result = check(original_file, new_file, variable_file, taboo_file)

    output_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')

    print(f"原创性检查完成：{output_file}")
    print(f"5-gram 重合率：{result['ngram_results']['5-gram']['overlap_ratio']:.2%}")
    print(f"8-gram 重合数：{result['ngram_results']['8-gram']['overlap_count']}")
    print(f"最长公共子串：{result['longest_common_substring']['length']} 字")
    print(f"真实变量残留：{len(result['variable_residues']['real_residues'])} 个")
    print(f"潜在残留(7字+)：{len(result['variable_residues']['potential_7plus'])} 个")
    print(f"日常短语残留(4-6字)：{result['variable_residues']['potential_4_6_count']} 个（高误报率，仅供参考）")
    print(f"句子结构相似度：{result['sentence_structure_similarity']['score']:.2%}")
    print(f"高风险段落：{len(result['high_overlap_paragraphs'])} 个")
    # v5.0 新增输出
    print(f"骨架相似度：{result['skeleton_similarity']['similarity']:.2%} / 目标 <50% / {'通过' if result['skeleton_similarity']['pass'] else '未通过'}")
    print(f"情绪曲线DTW：{result['emotion_curve_similarity']['normalized_distance']:.4f} / {'通过' if result['emotion_curve_similarity']['pass'] else '未通过'}")
    print(f"密度分布相关：{result['density_distribution_similarity']['correlation']:.4f} / 目标 <0.6 / {'通过' if result['density_distribution_similarity']['pass'] else '未通过'}")
    if result.get('taboo_hits'):
        print(f"同义替换禁忌命中：{len(result['taboo_hits'])} 个")
    print(f"最终结果：{'通过' if result['pass'] else '未通过'}")


if __name__ == '__main__':
    main()