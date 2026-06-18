"""
variable_annotator.py
关节点/变量标注工具
输出：换元清单 JSON
"""

import re
import json
import sys
from pathlib import Path
from encoding_utils import read_text_safe


def count_chinese_chars(text):
    return len(re.findall(r'[\u4e00-\u9fff]', text))


def extract_entities(text):
    """简单实体提取（基于常见模式，过滤常见虚词）"""
    entities = {
        'person': [],
        'location': [],
        'time': [],
        'object': []
    }

    # 常见虚词/无意义片段，需要过滤
    common_words = set([
        '什么', '怎么', '没有', '知道', '自己', '以为', '可以', '这么', '那么',
        '一个', '一种', '一样', '一直', '一天', '一年', '一次', '一句', '一刻',
        '看着', '走着', '来了', '去了', '坐下', '起来', '出去', '进来', '说了',
        '一句', '东西', '十五岁', '二十岁', '三十岁', '六十岁', '学教师', '了一句',
        '台后面', '个月', '坐在', ' his', ' her', ' the'
    ])

    def is_valid_entity(text):
        if text in common_words:
            return False
        if len(text) < 2:
            return False
        # 过滤纯数字或数字开头
        if re.match(r'^\d', text):
            return False
        # 过滤包含常见无意义片段的
        for cw in common_words:
            if cw in text and len(text) <= len(cw) + 2:
                return False
        return True

    # 人名：通过简单规则 + 常见姓氏提示（非常粗略，需人工审核）
    # 优先识别：叫[姓名]、[姓名]说/问/答
    person_patterns = []
    # 叫 X X
    person_patterns.extend(re.findall(r'叫([\u4e00-\u9fff]{2,3})(?=[，。！？])', text))
    # X 说 / X 问 / X 答
    person_patterns.extend(re.findall(r'([\u4e00-\u9fff]{2,3})(?=[\s，。！？]{0,3}[说问道答])', text))
    # 人名姓氏 + 名字（粗略）
    person_patterns.extend(re.findall(r'[\u4e00-\u9fff]{2,3}(?=[，。！？：\u201c])', text))
    
    filtered_persons = []
    for p in person_patterns:
        if is_valid_entity(p) and p not in filtered_persons:
            filtered_persons.append(p)
    entities['person'] = filtered_persons[:15]

    # 地点：包含常见地名后缀
    location_keywords = ['村', '城', '镇', '街', '路', '巷', '区', '县', '市', '省', '国', '店', '馆', '房', '屋', '楼', '院', '阁', '场', '站']
    for kw in location_keywords:
        matches = re.findall(r'[\u4e00-\u9fff]{1,4}' + kw, text)
        for m in matches:
            if is_valid_entity(m) and m not in entities['location']:
                entities['location'].append(m)
    entities['location'] = entities['location'][:15]

    # 时间
    time_patterns = re.findall(r'\d{1,4}年|\d{1,2}月|\d{1,2}日|三年前|五年前|十年前|三十年前|那天|昨夜|今晨|黄昏|黎明|隔天|第二天|几天后', text)
    entities['time'] = list(set(time_patterns))[:15]

    # 物体：包含常见物品后缀
    object_keywords = ['信', '表', '册', '书', '笔', '纸', '照片', '票', '钱', '包', '枪', '刀', '伞', '灯', '门', '窗', '钥匙', '手机', '电话', '箱子', '本子', '围巾', '伞', '戒指', '项链', '怀表', '名片', '纸条']
    for kw in object_keywords:
        matches = re.findall(r'[\u4e00-\u9fff]{0,3}' + kw, text)
        for m in matches:
            if is_valid_entity(m) and m not in entities['object']:
                entities['object'].append(m)
    entities['object'] = entities['object'][:15]

    return entities


def extract_dialogue(text):
    """提取对话（支持中文引号 "" 和 '' 以及英文引号）"""
    dialogue = []
    dialogue.extend(re.findall(r'[\u201c]([^\u201d]+)[\u201d]', text))  # 中文双引号
    dialogue.extend(re.findall(r'[\u2018]([^\u2019]+)[\u2019]', text))  # 中文单引号
    dialogue.extend(re.findall(r'[""]([^""]+)[""]', text))  # 英文双引号
    dialogue.extend(re.findall(r"['']([^'']+)['']", text))  # 英文单引号
    dialogue.extend(re.findall(r'[\u300c]([^\u300d]+)[\u300d]', text))  # 中文角括号「」
    dialogue.extend(re.findall(r'[\u300e]([^\u300f]+)[\u300f]', text))  # 中文双角括号『』
    return dialogue


def create_variable_list(text):
    """创建换元清单"""
    entities = extract_entities(text)
    dialogues = extract_dialogue(text)

    variables = []
    var_id = 1

    for p in entities['person'][:10]:
        variables.append({
            'id': f'V{var_id:03d}',
            'type': '人物',
            'original': p,
            'function': '待判断',
            'new_design': '待设计',
            'replaced': False
        })
        var_id += 1

    for loc in entities['location'][:10]:
        variables.append({
            'id': f'V{var_id:03d}',
            'type': '地点',
            'original': loc,
            'function': '待判断',
            'new_design': '待设计',
            'replaced': False
        })
        var_id += 1

    for t in entities['time'][:10]:
        variables.append({
            'id': f'V{var_id:03d}',
            'type': '时间',
            'original': t,
            'function': '待判断',
            'new_design': '待设计',
            'replaced': False
        })
        var_id += 1

    for obj in entities['object'][:10]:
        variables.append({
            'id': f'V{var_id:03d}',
            'type': '道具/意象',
            'original': obj,
            'function': '待判断',
            'new_design': '待设计',
            'replaced': False
        })
        var_id += 1

    for i, d in enumerate(dialogues[:10], 1):
        if len(d) >= 5:
            variables.append({
                'id': f'V{var_id:03d}',
                'type': '台词',
                'original': d,
                'function': '待判断',
                'new_design': '待设计',
                'replaced': False
            })
            var_id += 1

    return {
        'variable_count': len(variables),
        'variables': variables,
        'note': '本清单为初稿，需要人工审核和补充。建议使用 LLM 参考 prompts/p02-variable-annotate.md 完善。'
    }


def main():
    if len(sys.argv) < 2:
        print("用法: python variable_annotator.py <原文文件.md> [输出文件.json]")
        sys.exit(1)

    input_file = Path(sys.argv[1])
    output_file = Path(sys.argv[2]) if len(sys.argv) > 2 else input_file.with_suffix('.variables.json')

    text = read_text_safe(input_file)
    if text.startswith('---'):
        parts = text.split('---', 2)
        if len(parts) >= 3:
            text = parts[2]

    variable_list = create_variable_list(text)

    output_file.write_text(json.dumps(variable_list, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"换元清单初稿生成：{output_file}")
    print(f"识别到 {variable_list['variable_count']} 个潜在变量")
    print("请人工审核并补充遗漏变量")


if __name__ == '__main__':
    main()
