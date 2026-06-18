"""
quality_report.py
统一质量报告工具（v1.0）
集成字数分析、原创性检查、反检测检查，输出统一HTML+JSON报告

用法:
    python quality_report.py <原文文件> <新篇文件> [换元清单.json] [禁忌清单.json]

输出:
    - quality_report.json: 完整JSON报告
    - quality_report.html: 可视化HTML报告
"""

import re
import json
import sys
import math
import statistics
from pathlib import Path
from datetime import datetime
from encoding_utils import read_text_safe


def count_chinese_chars(text):
    return len(re.findall(r'[\u4e00-\u9fff]', text))


def clean_text(text):
    if text.startswith('---'):
        parts = text.split('---', 2)
        if len(parts) >= 3:
            text = parts[2]
    return re.sub(r'[^\u4e00-\u9fffa-zA-Z0-9]', '', text)


def split_paragraphs(text):
    paragraphs = re.split(r'\n\s*\n', text)
    return [p.strip() for p in paragraphs if p.strip()]


def split_sentences(text):
    sentences = re.split(r'[。！？…]+', text)
    return [s.strip() for s in sentences if s.strip()]


def generate_html_report(data):
    """生成可视化HTML报告"""
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>质量报告 - {data['timestamp']}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f5f5f5; padding: 20px; }}
        .container {{ max-width: 900px; margin: 0 auto; }}
        h1 {{ text-align: center; margin-bottom: 20px; color: #333; }}
        .card {{ background: white; border-radius: 8px; padding: 20px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        .card h2 {{ font-size: 18px; margin-bottom: 12px; color: #444; border-bottom: 2px solid #eee; padding-bottom: 8px; }}
        .pass {{ color: #2ecc71; font-weight: bold; }}
        .fail {{ color: #e74c3c; font-weight: bold; }}
        .warn {{ color: #f39c12; font-weight: bold; }}
        table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        th, td {{ padding: 8px 12px; text-align: left; border-bottom: 1px solid #eee; }}
        th {{ background: #f8f8f8; font-weight: 600; }}
        .metric {{ display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid #f0f0f0; }}
        .metric-value {{ font-weight: bold; font-size: 18px; }}
        .progress-bar {{ background: #eee; border-radius: 4px; height: 8px; margin-top: 4px; }}
        .progress-fill {{ height: 100%; border-radius: 4px; }}
        .details {{ font-size: 13px; color: #666; margin-top: 4px; }}
        .overall {{ text-align: center; font-size: 24px; padding: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>质量报告</h1>
        <p style="text-align:center; color:#999; margin-bottom:20px;">{data['timestamp']}</p>
"""

    overall_pass = data.get('overall_pass', False)
    overall_class = 'pass' if overall_pass else 'fail'
    overall_text = '通过' if overall_pass else '未通过'
    html += f"""        <div class="overall card"><span class="{overall_class}">最终结果：{overall_text}</span></div>"""

    html += """        <div class="card"><h2>📊 总览</h2>"""
    metrics = data.get('summary', {})
    for key, value in metrics.items():
        status_class = value.get('class', '')
        html += f"""<div class="metric"><span>{key}</span><span class="metric-value {status_class}">{value['value']}</span></div>"""
    html += """</div>"""

    if data.get('word_count'):
        html += """        <div class="card"><h2>📝 字数对齐</h2><table><tr><th>段落</th><th>目标</th><th>实际</th><th>偏差</th><th>状态</th></tr>"""
        for p in data['word_count'].get('paragraphs', []):
            status_class = 'pass' if p['status'] == 'ok' else 'fail'
            html += f"""<tr><td>第{p['index']}段</td><td>{p['target']}</td><td>{p['actual']}</td><td>{p.get('deviation_ratio', 'N/A')}</td><td class="{status_class}">{p['status']}</td></tr>"""
        html += """</table></div>"""

    if data.get('originality'):
        orig = data['originality']
        html += """        <div class="card"><h2>🔍 原创性</h2>"""
        html += f"""<div class="metric"><span>5-gram 重合率</span><span class="metric-value {orig.get('ngram5_class', '')}">{orig.get('ngram5_ratio', 'N/A')}</span></div>"""
        html += f"""<div class="metric"><span>8-gram 重合数</span><span class="metric-value {orig.get('ngram8_class', '')}">{orig.get('ngram8_count', 'N/A')}</span></div>"""
        html += f"""<div class="metric"><span>最长公共子串</span><span class="metric-value {orig.get('lcs_class', '')}">{orig.get('lcs_length', 'N/A')} 字</span></div>"""
        html += f"""<div class="metric"><span>真实变量残留</span><span class="metric-value {orig.get('residue_class', '')}">{orig.get('real_residue_count', 'N/A')} 个</span></div>"""
        html += f"""<div class="metric"><span>潜在残留(7+字)</span><span class="metric-value {orig.get('potential7_class', '')}">{orig.get('potential7_count', 'N/A')} 个</span></div>"""
        html += f"""<div class="metric"><span>句子结构相似度</span><span class="metric-value {orig.get('struct_class', '')}">{orig.get('struct_similarity', 'N/A')}</span></div>"""
        html += """</div>"""

    if data.get('anti_detection'):
        ad = data['anti_detection']
        html += """        <div class="card"><h2>🛡️ 反检测</h2>"""
        html += f"""<div class="metric"><span>突发性 Burstiness</span><span class="metric-value {ad.get('burstiness_class', '')}">{ad.get('burstiness', 'N/A')}</span></div>"""
        html += f"""<div class="metric"><span>短句占比</span><span>{ad.get('short_ratio', 'N/A')}</span></div>"""
        html += f"""<div class="metric"><span>长短句交替率</span><span>{ad.get('alternation_rate', 'N/A')}</span></div>"""
        html += f"""<div class="metric"><span>硬黑名单 AI 词</span><span class="metric-value {ad.get('hard_ai_class', '')}">{ad.get('hard_ai_count', 'N/A')} 个</span></div>"""
        html += f"""<div class="metric"><span>软黑名单 AI 词</span><span class="metric-value {ad.get('soft_ai_class', '')}">{ad.get('soft_ai_count', 'N/A')} 次</span></div>"""
        html += f"""<div class="metric"><span>硬模式化标记</span><span class="metric-value {ad.get('hard_pattern_class', '')}">{ad.get('hard_pattern_count', 'N/A')} 个</span></div>"""
        html += f"""<div class="metric"><span>软模式化标记</span><span class="metric-value {ad.get('soft_pattern_class', '')}">{ad.get('soft_pattern_count', 'N/A')} 个</span></div>"""
        html += """</div>"""

    if data.get('high_risk_paragraphs'):
        html += """        <div class="card"><h2>⚠️ 高风险段落</h2><table><tr><th>段落</th><th>指标</th><th>详情</th></tr>"""
        for p in data['high_risk_paragraphs']:
            html += f"""<tr><td>第{p['paragraph']}段</td><td>{p['indicators']}</td><td>{p['details']}</td></tr>"""
        html += """</table></div>"""

    if data.get('priority_fixes'):
        html += """        <div class="card"><h2>🔧 优先修复</h2><table><tr><th>优先级</th><th>问题</th><th>建议</th></tr>"""
        for fix in data['priority_fixes']:
            html += f"""<tr><td>{fix['priority']}</td><td>{fix['issue']}</td><td>{fix['suggestion']}</td></tr>"""
        html += """</table></div>"""

    html += """    </div></body></html>"""
    return html


def run_quality_check(original_file, new_file, variable_file=None, taboo_file=None):
    """运行完整质量检查"""
    original_text = read_text_safe(original_file)
    new_text = read_text_safe(new_file)

    orig_clean = clean_text(original_text)
    new_clean = clean_text(new_text)

    sys.path.insert(0, str(Path(__file__).parent))

    from word_count_analyzer import analyze_text, generate_budget_table
    from word_count_adjuster import analyze_deviation, split_paragraphs as wca_split_paragraphs
    if (Path(__file__).parent / 'originality_checker.py').exists():
        import originality_checker as oc
    else:
        oc = None
    if (Path(__file__).parent / 'anti_detection_checker.py').exists():
        import anti_detection_checker as adc
    else:
        adc = None

    orig_analysis = analyze_text(original_text)

    new_text_clean_for_budget = new_text
    if new_text_clean_for_budget.startswith('---'):
        parts = new_text_clean_for_budget.split('---', 2)
        if len(parts) >= 3:
            new_text_clean_for_budget = parts[2]

    budget = generate_budget_table(orig_analysis)

    budget_data = json.loads(json.dumps(budget))
    deviation_result = analyze_deviation(new_text_clean_for_budget, budget_data)
    word_count_data = deviation_result

    orig_data = None
    if oc:
        result = oc.check(original_file, new_file, variable_file, taboo_file)
        orig_data = result

    ad_result = None
    if adc:
        text_for_ad = new_text
        if text_for_ad.startswith('---'):
            parts = text_for_ad.split('---', 2)
            if len(parts) >= 3:
                text_for_ad = parts[2]
        ad_result = adc.check(text_for_ad)

    summary = {}
    overall_pass = True

    total_dev = word_count_data.get('total_deviation_ratio', 0)
    total_actual = word_count_data.get('total_actual', 0)
    total_target = word_count_data.get('total_target', 0)
    wc_pass = abs(total_dev) <= 0.05
    summary['总字数'] = {'value': f'{total_actual}/{total_target}', 'class': 'pass' if wc_pass else 'fail'}
    summary['字数偏差'] = {'value': f'{total_dev:.2%}', 'class': 'pass' if wc_pass else 'fail'}
    if not wc_pass:
        overall_pass = False

    if orig_data:
        n5_ratio = orig_data['ngram_results']['5-gram']['overlap_ratio']
        n5_pass = n5_ratio < 0.05
        summary['5-gram重合率'] = {'value': f'{n5_ratio:.2%}', 'class': 'pass' if n5_pass else 'fail'}
        if not n5_pass:
            overall_pass = False

        n8_count = orig_data['ngram_results']['8-gram']['overlap_count']
        n8_pass = n8_count < 10
        summary['8-gram重合数'] = {'value': str(n8_count), 'class': 'pass' if n8_pass else 'fail'}
        if not n8_pass:
            overall_pass = False

        real_res = len(orig_data['variable_residues']['real_residues'])
        res_pass = real_res == 0
        summary['真实变量残留'] = {'value': f'{real_res}个', 'class': 'pass' if res_pass else 'fail'}
        if not res_pass:
            overall_pass = False

        pot7 = len(orig_data['variable_residues']['potential_7plus'])
        pot7_pass = pot7 <= 5
        summary['潜在残留(7+字)'] = {'value': f'{pot7}个', 'class': 'pass' if pot7_pass else 'fail'}

        lcs_len = orig_data['longest_common_substring']['length']
        lcs_pass = lcs_len < 8
        summary['最长公共子串'] = {'value': f'{lcs_len}字', 'class': 'pass' if lcs_pass else 'fail'}
        if not lcs_pass:
            overall_pass = False

        struct_sim = orig_data['sentence_structure_similarity']['score']
        struct_pass = struct_sim < 0.5
        summary['句子结构相似度'] = {'value': f'{struct_sim:.2%}', 'class': 'pass' if struct_pass else 'fail'}

    if ad_result:
        burstiness = ad_result['burstiness']['value']
        bur_pass = ad_result['burstiness']['pass']
        summary['突发性'] = {'value': f'{burstiness}', 'class': 'pass' if bur_pass else 'fail'}
        if not bur_pass:
            overall_pass = False

        short_r = ad_result['sentence_rhythm']['short_ratio']
        alt_r = ad_result['sentence_rhythm']['alternation_rate']
        summary['短句占比'] = {'value': f'{short_r:.2%}', 'class': 'pass' if short_r >= 0.15 else 'warn'}
        summary['长短句交替'] = {'value': f'{alt_r:.2%}', 'class': 'pass' if alt_r >= 0.10 else 'warn'}

        hard_ai = ad_result['ai_words']['hard']['count']
        summary['硬AI特征词'] = {'value': f'{hard_ai}个', 'class': 'pass' if hard_ai == 0 else 'fail'}
        if hard_ai > 0:
            overall_pass = False

        soft_ai = ad_result['ai_words']['soft']['count']
        summary['软AI特征词'] = {'value': f'{soft_ai}次', 'class': 'pass' if soft_ai <= 5 else 'warn'}

        # v5.0 新增反检测指标
        if 'paragraph_variance' in ad_result:
            pv = ad_result['paragraph_variance']
            summary['段落方差比'] = {'value': f"{pv.get('ratio', 'N/A')}", 'class': 'pass' if pv.get('pass') else 'fail'}
            if not pv.get('pass'):
                overall_pass = False
        
        if 'connector_diversity' in ad_result:
            cd = ad_result['connector_diversity']
            summary['连接词多样性'] = {'value': f"{cd.get('diversity_rate', 0):.2%}", 'class': 'pass' if cd.get('pass') else 'warn'}
        
        if 'density_fluctuation' in ad_result:
            df = ad_result['density_fluctuation']
            summary['信息密度波动'] = {'value': f"{df.get('fluctuation_rate', 0):.2%}", 'class': 'pass' if df.get('pass') else 'warn'}
        
        if 'dialogue_fragmentation' in ad_result:
            dg = ad_result['dialogue_fragmentation']
            summary['对话碎片化'] = {'value': f"{dg.get('fragmentation_rate', 0):.2%}", 'class': 'pass' if dg.get('pass') else 'warn'}
        
        if 'digression_density' in ad_result:
            dd = ad_result['digression_density']
            summary['闲笔密度'] = {'value': f"{dd.get('density_per_1000', 0):.2f}/千字", 'class': 'pass' if dd.get('pass') else 'warn'}
        
        if 'perspective_jump' in ad_result:
            pj = ad_result['perspective_jump']
            summary['视角跳切'] = {'value': f"{pj.get('jump_count', 0)}次", 'class': 'pass' if pj.get('pass') else 'warn'}

    # v5.0 新增原创性指标
    if orig_data:
        if 'skeleton_similarity' in orig_data:
            ss = orig_data['skeleton_similarity']
            summary['骨架相似度'] = {'value': f"{ss.get('similarity', 0):.2%}", 'class': 'pass' if ss.get('pass') else 'fail'}
            if not ss.get('pass'):
                overall_pass = False
        
        if 'emotion_curve_similarity' in orig_data:
            ec = orig_data['emotion_curve_similarity']
            summary['情绪曲线差异'] = {'value': f"{ec.get('normalized_distance', 0):.4f}", 'class': 'pass' if ec.get('pass') else 'warn'}
        
        if 'density_distribution_similarity' in orig_data:
            ds = orig_data['density_distribution_similarity']
            summary['密度分布相关'] = {'value': f"{ds.get('correlation', 0):.4f}", 'class': 'pass' if ds.get('pass') else 'warn'}

    high_risk = []
    if orig_data and orig_data.get('high_overlap_paragraphs'):
        for p in orig_data['high_overlap_paragraphs']:
            indicators = []
            details = []
            if p['ngram_overlap'] > 0.1:
                indicators.append('N-gram重合高')
                details.append(f"5-gram重合{p['ngram_overlap']:.2%}")
            if p['lcs_length'] > 15:
                indicators.append('LCS过长')
                details.append(f"LCS {p['lcs_length']}字")
            high_risk.append({
                'paragraph': p['paragraph'],
                'indicators': ', '.join(indicators) if indicators else '字数偏差大',
                'details': '; '.join(details) if details else ''
            })

    for pd in word_count_data.get('paragraphs', []):
        if pd['status'] != 'ok':
            if not any(hr['paragraph'] == pd['index'] for hr in high_risk):
                high_risk.append({
                    'paragraph': pd['index'],
                    'indicators': f"字数偏差{pd['deviation_ratio']:.2%}",
                    'details': f"目标{pd['target']}字，实际{pd['actual']}字"
                })

    priority_fixes = []
    if orig_data:
        real_res = len(orig_data['variable_residues']['real_residues'])
        if real_res > 0:
            priority_fixes.append({'priority': 'P0', 'issue': f'变量残留{real_res}个', 'suggestion': '立即替换原文变量'})
        lcs_len = orig_data['longest_common_substring']['length']
        if lcs_len >= 8:
            lcs_content = orig_data['longest_common_substring']['content'][:30]
            priority_fixes.append({'priority': 'P0', 'issue': f'最长公共子串{lcs_len}字', 'suggestion': f'重写包含"{lcs_content}"的段落'})
        n5 = orig_data['ngram_results']['5-gram']['overlap_ratio']
        if n5 >= 0.05:
            priority_fixes.append({'priority': 'P0', 'issue': f'5-gram重合率{n5:.2%}', 'suggestion': '对高重合段落进行功能等价重写'})

    if abs(word_count_data.get('total_deviation_ratio', 0)) > 0.05:
        priority_fixes.append({'priority': 'P1', 'issue': f'字数偏差{word_count_data["total_deviation_ratio"]:.2%}', 'suggestion': '按段落预算逐段扩写或压缩'})

    if ad_result:
        if not ad_result['burstiness']['pass']:
            priority_fixes.append({'priority': 'P1', 'issue': f'突发性{ad_result["burstiness"]["value"]}', 'suggestion': '增加长短句交错，插入2-8字短句和25字+长句'})
        hard_ai = ad_result['ai_words']['hard']['count']
        if hard_ai > 0:
            priority_fixes.append({'priority': 'P1', 'issue': f'硬黑名单AI词{hard_ai}个', 'suggestion': '删除或替换硬黑名单词'})

    report = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'original_file': str(original_file),
        'new_file': str(new_file),
        'overall_pass': overall_pass,
        'summary': summary,
        'word_count': word_count_data,
        'originality': {
            'ngram5_ratio': f"{orig_data['ngram_results']['5-gram']['overlap_ratio']:.2%}" if orig_data else 'N/A',
            'ngram5_class': 'pass' if orig_data and orig_data['ngram_results']['5-gram']['overlap_ratio'] < 0.05 else 'fail',
            'ngram8_count': orig_data['ngram_results']['8-gram']['overlap_count'] if orig_data else 'N/A',
            'ngram8_class': 'pass' if orig_data and orig_data['ngram_results']['8-gram']['overlap_count'] < 10 else 'fail',
            'lcs_length': orig_data['longest_common_substring']['length'] if orig_data else 'N/A',
            'lcs_class': 'pass' if orig_data and orig_data['longest_common_substring']['length'] < 8 else 'fail',
            'real_residue_count': len(orig_data['variable_residues']['real_residues']) if orig_data else 'N/A',
            'residue_class': 'pass' if orig_data and len(orig_data['variable_residues']['real_residues']) == 0 else 'fail',
            'potential7_count': len(orig_data['variable_residues']['potential_7plus']) if orig_data else 'N/A',
            'potential7_class': 'pass' if orig_data and len(orig_data['variable_residues']['potential_7plus']) <= 5 else 'fail',
            'struct_similarity': f"{orig_data['sentence_structure_similarity']['score']:.2%}" if orig_data else 'N/A',
            'struct_class': 'pass' if orig_data and orig_data['sentence_structure_similarity']['score'] < 0.5 else 'fail',
            # v5.0 新增
            'skeleton_similarity': f"{orig_data.get('skeleton_similarity', {}).get('similarity', 0):.2%}" if orig_data else 'N/A',
            'skeleton_class': 'pass' if orig_data and orig_data.get('skeleton_similarity', {}).get('pass') else 'fail',
            'emotion_dtw': f"{orig_data.get('emotion_curve_similarity', {}).get('normalized_distance', 0):.4f}" if orig_data else 'N/A',
            'emotion_class': 'pass' if orig_data and orig_data.get('emotion_curve_similarity', {}).get('pass') else 'fail',
            'density_corr': f"{orig_data.get('density_distribution_similarity', {}).get('correlation', 0):.4f}" if orig_data else 'N/A',
            'density_class': 'pass' if orig_data and orig_data.get('density_distribution_similarity', {}).get('pass') else 'fail',
        } if orig_data else {},
        'anti_detection': {
            'burstiness': ad_result['burstiness']['value'] if ad_result else 'N/A',
            'burstiness_class': 'pass' if ad_result and ad_result['burstiness']['pass'] else 'fail',
            'short_ratio': f"{ad_result['sentence_rhythm']['short_ratio']:.2%}" if ad_result else 'N/A',
            'alternation_rate': f"{ad_result['sentence_rhythm']['alternation_rate']:.2%}" if ad_result else 'N/A',
            'hard_ai_count': ad_result['ai_words']['hard']['count'] if ad_result else 'N/A',
            'hard_ai_class': 'pass' if ad_result and ad_result['ai_words']['hard']['count'] == 0 else 'fail',
            'soft_ai_count': ad_result['ai_words']['soft']['count'] if ad_result else 'N/A',
            'soft_ai_class': 'pass' if ad_result and ad_result['ai_words']['soft']['count'] <= 5 else 'warn',
            'hard_pattern_count': ad_result['patterns']['hard']['count'] if ad_result else 'N/A',
            'hard_pattern_class': 'pass' if ad_result and ad_result['patterns']['hard']['count'] == 0 else 'fail',
            'soft_pattern_count': ad_result['patterns']['soft']['count'] if ad_result else 'N/A',
            'soft_pattern_class': 'pass' if ad_result and ad_result['patterns']['soft']['count'] <= 3 else 'warn',
            # v5.0 新增
            'paragraph_variance': ad_result.get('paragraph_variance', {}).get('ratio') if ad_result else 'N/A',
            'paragraph_variance_class': 'pass' if ad_result and ad_result.get('paragraph_variance', {}).get('pass') else 'fail',
            'connector_diversity': f"{ad_result.get('connector_diversity', {}).get('diversity_rate', 0):.2%}" if ad_result else 'N/A',
            'connector_class': 'pass' if ad_result and ad_result.get('connector_diversity', {}).get('pass') else 'warn',
            'density_fluctuation': f"{ad_result.get('density_fluctuation', {}).get('fluctuation_rate', 0):.2%}" if ad_result else 'N/A',
            'density_fluc_class': 'pass' if ad_result and ad_result.get('density_fluctuation', {}).get('pass') else 'warn',
            'dialogue_fragmentation': f"{ad_result.get('dialogue_fragmentation', {}).get('fragmentation_rate', 0):.2%}" if ad_result else 'N/A',
            'dialogue_frag_class': 'pass' if ad_result and ad_result.get('dialogue_fragmentation', {}).get('pass') else 'warn',
            'digression_density': f"{ad_result.get('digression_density', {}).get('density_per_1000', 0):.2f}" if ad_result else 'N/A',
            'digression_class': 'pass' if ad_result and ad_result.get('digression_density', {}).get('pass') else 'warn',
            'perspective_jump': ad_result.get('perspective_jump', {}).get('jump_count') if ad_result else 'N/A',
            'perspective_class': 'pass' if ad_result and ad_result.get('perspective_jump', {}).get('pass') else 'warn',
        } if ad_result else {},
        'high_risk_paragraphs': high_risk,
        'priority_fixes': priority_fixes,
        'raw_originality': orig_data,
        'raw_anti_detection': ad_result,
        'raw_word_count': word_count_data
    }

    return report


def main():
    if len(sys.argv) < 3:
        print("用法: python quality_report.py <原文文件> <新篇文件> [换元清单.json] [禁忌清单.json]")
        print("说明: 集成字数分析、原创性检查、反检测检查，输出统一报告")
        sys.exit(1)

    original_file = Path(sys.argv[1])
    new_file = Path(sys.argv[2])
    variable_file = Path(sys.argv[3]) if len(sys.argv) > 3 else None
    taboo_file = Path(sys.argv[4]) if len(sys.argv) > 4 else None

    report = run_quality_check(original_file, new_file, variable_file, taboo_file)

    output_dir = new_file.parent / 'output'
    output_dir.mkdir(exist_ok=True)
    json_output = new_file.with_suffix('.quality.json')
    html_output = new_file.with_suffix('.quality.html')

    json_output.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding='utf-8')
    html_output.write_text(generate_html_report(report), encoding='utf-8')

    print(f"质量报告已生成：")
    print(f"  JSON: {json_output}")
    print(f"  HTML: {html_output}")
    print(f"\n最终结果：{'通过' if report['overall_pass'] else '未通过'}")
    print(f"\n摘要：")
    for key, value in report['summary'].items():
        status_map = {'pass': '[PASS]', 'warn': '[WARN]', 'fail': '[FAIL]'}
        status = status_map.get(value['class'], '[?]')
        print(f"  {status} {key}: {value['value']}")
    if report['priority_fixes']:
        print(f"\n优先修复：")
        for fix in report['priority_fixes']:
            print(f"  [{fix['priority']}] {fix['issue']} → {fix['suggestion']}")


if __name__ == '__main__':
    main()