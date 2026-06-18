"""
word_count_adjuster.py
字数对齐修正工具
检测段落字数偏差，给出扩写/压缩建议
"""

import re
import json
import sys
from pathlib import Path


def count_chinese_chars(text):
    return len(re.findall(r'[\u4e00-\u9fff]', text))


def split_paragraphs(text):
    """智能段落合并：按空行分段，无空行则合并连续行"""
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


def analyze_deviation(new_text, budget):
    """分析新篇与预算的偏差"""
    paragraphs = split_paragraphs(new_text)
    budget_paras = budget.get('paragraphs', [])
    deviations = []
    misaligned = len(paragraphs) != len(budget_paras)
    
    for i, p in enumerate(paragraphs, 1):
        actual = count_chinese_chars(p)
        budget_para = next((b for b in budget_paras if b['index'] == i), None)
        
        if budget_para:
            target = budget_para['target_chars']
            min_chars = budget_para['min_chars']
            max_chars = budget_para['max_chars']
            deviation = actual - target
            deviation_ratio = deviation / target if target > 0 else 0
            
            status = 'ok'
            if actual < min_chars:
                status = 'short'
            elif actual > max_chars:
                status = 'long'
            
            deviations.append({
                'index': i,
                'target': target,
                'actual': actual,
                'deviation': deviation,
                'deviation_ratio': round(deviation_ratio, 4),
                'status': status,
                'suggestion': generate_suggestion(status, abs(deviation))
            })
    
    total_actual = count_chinese_chars(new_text)
    total_target = budget['target_total']
    total_deviation_ratio = (total_actual - total_target) / total_target if total_target > 0 else 0
    
    return {
        'total_actual': total_actual,
        'total_target': total_target,
        'total_deviation_ratio': round(total_deviation_ratio, 4),
        'misaligned': misaligned,
        'paragraphs': deviations
    }


def generate_suggestion(status, deviation):
    """生成修正建议"""
    if status == 'ok':
        return '字数符合预算，无需调整'
    elif status == 'short':
        if deviation < 20:
            return '略短：可增加 1-2 个感官细节或心理活动'
        elif deviation < 50:
            return '偏短：可增加环境描写、对话反应或内心独白'
        else:
            return '严重偏短：需要补充一个细节片段或扩展对话'
    elif status == 'long':
        if deviation < 20:
            return '略长：可删除 1-2 个冗余形容词'
        elif deviation < 50:
            return '偏长：可合并简单句、删除过渡词或压缩对话提示'
        else:
            return '严重偏长：需要删减次要描写或合并句子'


def main():
    if len(sys.argv) < 3:
        print("用法: python word_count_adjuster.py <新篇文件.md> <字数预算.json> [输出报告.json]")
        print("说明: 字数预算文件可以是 word_count_analyzer.py 生成的完整 analysis.json（含 budget 字段），也可以是单独的 budget.json")
        sys.exit(1)
    
    new_file = Path(sys.argv[1])
    budget_file = Path(sys.argv[2])
    output_file = Path(sys.argv[3]) if len(sys.argv) > 3 else new_file.with_suffix('.deviation.json')
    
    new_text = new_file.read_text(encoding='utf-8')
    if new_text.startswith('---'):
        parts = new_text.split('---', 2)
        if len(parts) >= 3:
            new_text = parts[2]
    
    budget_data = json.loads(budget_file.read_text(encoding='utf-8'))
    # 兼容完整 analysis.json（含 analysis + budget）和单独的 budget.json
    if 'budget' in budget_data and isinstance(budget_data['budget'], dict):
        budget = budget_data['budget']
    else:
        budget = budget_data
    
    result = analyze_deviation(new_text, budget)
    
    output_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"字数偏差分析完成：{output_file}")
    print(f"新篇总字数：{result['total_actual']} / 目标：{result['total_target']} / 偏差：{result['total_deviation_ratio']:.2%}")
    
    for p in result['paragraphs']:
        if p['status'] != 'ok':
            print(f"第 {p['index']} 段：实际 {p['actual']} / 目标 {p['target']} / 偏差 {p['deviation_ratio']:.2%} / {p['suggestion']}")


if __name__ == '__main__':
    main()
