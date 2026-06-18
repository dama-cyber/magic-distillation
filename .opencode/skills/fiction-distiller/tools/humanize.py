"""
humanize.py
人类化后处理工具 v1.0
在生成初稿后、验证前执行，主动制造"有人味的混乱"

用法:
    python humanize.py <输入文件> [输出文件] [--strength low|medium|high]

输出:
    - 人类化后的文本文件
    - .humanize.json 处理报告
"""

import re
import json
import random
import sys
from pathlib import Path
from encoding_utils import read_text_safe


# ============ 配置 ============

CONFIG_PRESETS = {
    'low': {
        'micro_sentence_density': 0.002,
        'paragraph_variance_ratio': 2.0,
        'dialogue_fragmentation_rate': 0.15,
        'digression_density': 0.0003,
        'imperfection_rate': 0.001,
        'connector_replace_rate': 0.3,
    },
    'medium': {
        'micro_sentence_density': 0.004,
        'paragraph_variance_ratio': 3.0,
        'dialogue_fragmentation_rate': 0.30,
        'digression_density': 0.0005,
        'imperfection_rate': 0.002,
        'connector_replace_rate': 0.6,
    },
    'high': {
        'micro_sentence_density': 0.006,
        'paragraph_variance_ratio': 4.0,
        'dialogue_fragmentation_rate': 0.45,
        'digression_density': 0.0008,
        'imperfection_rate': 0.003,
        'connector_replace_rate': 0.9,
    },
}

# 连接词替换表：标准 → 口语化候选列表
CONNECTOR_MAP = {
    '然而': ['可', '不过', '话说回来', '倒也是', '但话说回来'],
    '此外': ['还有', '再说', '顺便提一句', '另外呢'],
    '因此': ['于是', '所以', '这下', '到头来', '就这么着'],
    '与此同时': ['那会儿', '正当这时', '偏偏这时候', '说来也巧'],
    '最后': ['临了', '末了', '到头来', '到头来还是', '最后呢'],
    '首先': ['一开始', '起先', '开头呢'],
    '其次': ['接着', '然后呢', '再一个'],
    '综上所述': ['总之', '说白了', '说到底'],
    '值得注意的是': ['有意思的是', '说来怪了', '蹊跷的是'],
    '不可否认的是': ['说实在的', '讲真', '平心而论'],
}

# 碎片化对话模板（中文语境）
DIALOGUE_FRAGMENTS = [
    '（打断）"{speaker}你别——"',
    '（沉默）{speaker}张了张嘴，没出声。',
    '（重复）"我、我……"',
    '（口吃）"那、那个……"',
    '（答非所问）"{question}""天挺热的。"',
    '（省略）"反正就是……那样吧。"',
    '（反问）"你说呢？"',
    '（自言自语）"……算了。"',
]

# 闲笔模板
DIGRESSION_TEMPLATES = [
    '窗外的{plant}那年刚栽，{state}，她记得{memory}。',
    '空气里有{smell}的味道，{time}的{place}总是这样。',
    '{item}上落了灰，{detail}，谁也没注意到。',
    '远处传来{sound}，{distance}，像是{comparison}。',
    '墙角有{insect}爬过，{action}，{thought}。',
]

DIGRESSION_FILLERS = {
    'plant': ['梧桐', '槐树', '石榴', '爬山虎', '夹竹桃'],
    'state': ['叶子还稀稀拉拉的', '枝干细得像根筷子', '歪歪扭扭地支棱着', '才到腰那么高'],
    'memory': ['小时候外婆家也有这么一棵', '父亲说过这树活不长', '去年冬天差点被冻死'],
    'smell': ['霉味', '油烟', '消毒水', '桂花', '雨后泥土'],
    'time': ['这个季节', '傍晚', '大清早', '下雨天'],
    'place': ['老小区', '镇上', '厂区', '家属院'],
    'item': ['窗台', '暖气片', '配电箱', '信报箱'],
    'detail': ['厚厚的一层', '被人用手指划出道子', '贴着半张褪色的广告'],
    'sound': ['锯木声', '小孩哭', '广播体操', '铁门拉动'],
    'distance': ['隔了两条街', '从楼后传来的', '时断时续的'],
    'comparison': ['有人在拆家具', '猫被踩了尾巴', '旧收音机串台'],
    'insect': ['一只蟑螂', '几只蚂蚁', '一只蛾子'],
    'action': ['不慌不忙地爬', '绕了个圈又回去了', '停在那儿不动了'],
    'thought': ['她盯着看了很久', '谁会在意这些呢', '这地方就这样'],
}


# ============ 核心函数 ============

def count_chinese_chars(text):
    return len(re.findall(r'[\u4e00-\u9fff]', text))


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


def split_sentences(text):
    """按标点分句"""
    sentences = re.split(r'[。！？…]+', text)
    return [s.strip() for s in sentences if s.strip()]


# ---------- 1. 注入极端短句 ----------

def inject_micro_sentences(text, density=0.004):
    """
    在段落内部或段间插入 1-3 字超短句
    density: 每字的出现概率（0.004 = 每1000字约4个）
    """
    sentences = split_sentences(text)
    if len(sentences) < 3:
        return text
    
    micro_pool = ['哦。', '嗯。', '没。', '完了。', '算了。', '然后呢。', '是吧。', '才怪。', '得了。', '就这样。']
    result_sentences = []
    insert_count = 0
    
    for i, sent in enumerate(sentences):
        result_sentences.append(sent)
        cn_count = count_chinese_chars(sent)
        # 以一定概率在句后插入超短句
        if random.random() < density * cn_count and insert_count < max(3, int(count_chinese_chars(text) * density)):
            result_sentences.append(random.choice(micro_pool))
            insert_count += 1
    
    return '。'.join(result_sentences) + ('。' if not text.endswith(('。', '！', '？', '…')) else '')


# ---------- 2. 调整段落长度方差 ----------

def adjust_paragraph_variance(text, target_ratio=3.0):
    """
    确保最长段落 / 最短段落 >= target_ratio
    策略：如果方差不足，拆分最长段或合并最短段
    """
    paragraphs = split_paragraphs(text)
    if len(paragraphs) < 3:
        return text
    
    lengths = [count_chinese_chars(p) for p in paragraphs]
    max_len = max(lengths)
    min_len = min(lengths)
    
    if max_len / max(min_len, 1) >= target_ratio:
        return text  # 已达标
    
    # 策略：拆分最长段落（在第一个句号后拆分）
    max_idx = lengths.index(max_len)
    longest = paragraphs[max_idx]
    sentences = split_sentences(longest)
    
    if len(sentences) >= 3:
        mid = len(sentences) // 2
        part1 = '。'.join(sentences[:mid]) + '。'
        part2 = '。'.join(sentences[mid:]) + '。'
        
        new_paragraphs = paragraphs[:max_idx] + [part1, part2] + paragraphs[max_idx+1:]
        return '\n\n'.join(new_paragraphs)
    
    return text


# ---------- 3. 替换连接词 ----------

def replace_connectors(text, replace_rate=0.6):
    """
    将标准连接词替换为口语化版本
    replace_rate: 替换比例
    """
    for standard, colloquials in CONNECTOR_MAP.items():
        # 找到所有出现位置
        pattern = re.escape(standard)
        matches = list(re.finditer(pattern, text))
        
        # 随机选择一部分进行替换
        to_replace = random.sample(matches, min(int(len(matches) * replace_rate), len(matches))) if matches else []
        
        # 从后往前替换，避免位置偏移
        for match in sorted(to_replace, key=lambda m: m.start(), reverse=True):
            replacement = random.choice(colloquials)
            start, end = match.start(), match.end()
            text = text[:start] + replacement + text[end:]
    
    return text


# ---------- 4. 对话碎片化 ----------

def fragment_dialogue(text, fragmentation_rate=0.30):
    """
    将部分完整对话改为碎片化形式（打断、沉默、重复等）
    fragmentation_rate: 碎片化比例
    """
    # 匹配对话模式："..."（引号内的内容）
    dialogue_pattern = re.compile(r'"([^"]{5,60})"')
    dialogues = list(dialogue_pattern.finditer(text))
    
    if not dialogues:
        return text
    
    # 选择要碎片化的对话
    to_fragment = random.sample(dialogues, min(max(1, int(len(dialogues) * fragmentation_rate)), len(dialogues)))
    
    for match in sorted(to_fragment, key=lambda m: m.start(), reverse=True):
        original = match.group(1)
        # 随机选择一种碎片化形式
        fragment_type = random.choice(['打断', '沉默', '重复', '省略', '反问'])
        
        if fragment_type == '打断':
            # 在句子中间打断
            words = list(original)
            if len(words) > 4:
                cut_point = random.randint(2, len(words) - 2)
                replacement = f'"{"".join(words[:cut_point])}"——'
            else:
                replacement = f'"{original}"——'
        elif fragment_type == '沉默':
            replacement = f'（沉默）'
        elif fragment_type == '重复':
            first_word = original[:2] if len(original) >= 2 else original
            replacement = f'"{first_word}、{first_word}……"'
        elif fragment_type == '省略':
            replacement = f'"……{original[-4:] if len(original) > 4 else original}"'
        elif fragment_type == '反问':
            replacement = f'"{original}？"'
        
        start, end = match.start(), match.end()
        text = text[:start] + replacement + text[end:]
    
    return text


# ---------- 5. 插入闲笔 ----------

def insert_digressions(text, density=0.0005):
    """
    在叙事中插入与主线无关的感官细节
    density: 每字的插入概率（0.0005 = 每2000字约1处）
    """
    paragraphs = split_paragraphs(text)
    total_chars = count_chinese_chars(text)
    target_inserts = max(1, int(total_chars * density))
    
    # 选择插入位置（避开开头和结尾段落）
    valid_indices = list(range(1, len(paragraphs) - 1)) if len(paragraphs) > 2 else []
    if not valid_indices:
        return text
    
    insert_positions = random.sample(valid_indices, min(target_inserts, len(valid_indices)))
    
    for idx in sorted(insert_positions, reverse=True):
        template = random.choice(DIGRESSION_TEMPLATES)
        # 填充模板
        digression = template
        for key, options in DIGRESSION_FILLERS.items():
            placeholder = '{' + key + '}'
            if placeholder in digression:
                digression = digression.replace(placeholder, random.choice(options), 1)
        
        paragraphs.insert(idx, digression)
    
    return '\n\n'.join(paragraphs)


# ---------- 6. 注入轻微不完美 ----------

def inject_minor_imperfections(text, rate=0.002):
    """
    制造轻微的人类写作不完美
    rate: 每字的出现概率
    """
    total_chars = count_chinese_chars(text)
    target_count = max(1, int(total_chars * rate))
    
    sentences = split_sentences(text)
    if len(sentences) < 3:
        return text
    
    # 选择要修改的句子
    candidates = list(range(len(sentences)))
    to_modify = random.sample(candidates, min(target_count, len(candidates)))
    
    for idx in sorted(to_modify, reverse=True):
        sent = sentences[idx]
        imperfection_type = random.choice(['runon', 'fragment', 'fuzzy'])
        
        if imperfection_type == 'runon' and '，' in sent:
            # 把某个逗号变成更口语化的连接
            sent = sent.replace('，', '，', 1)  # 保持不变，实际可以不做修改
            # 或者：制造一个逗号拼接
            if random.random() < 0.5:
                sent = sent.replace('。', '，', 1) if '。' in sent else sent
        elif imperfection_type == 'fragment':
            # 制造不完整句（用于内心独白或对话）
            if len(sent) > 10:
                sent = sent[:random.randint(5, min(15, len(sent)))] + '……'
        elif imperfection_type == 'fuzzy':
            # 加入模糊化表达
            fuzzy_phrases = ['好像', '大概', '也许', '说不清', '反正']
            if not any(p in sent for p in fuzzy_phrases):
                words = list(sent)
                insert_pos = random.randint(0, len(words))
                sent = ''.join(words[:insert_pos]) + random.choice(fuzzy_phrases) + ''.join(words[insert_pos:])
        
        sentences[idx] = sent
    
    return '。'.join(sentences) + '。'


# ============ 主入口 ============

def humanize(text: str, strength: str = 'medium', config: dict = None) -> tuple:
    """
    人类化主函数
    
    返回: (处理后的文本, 处理报告字典)
    """
    cfg = config or CONFIG_PRESETS.get(strength, CONFIG_PRESETS['medium'])
    report = {
        'strength': strength,
        'original_chars': count_chinese_chars(text),
        'steps': {}
    }
    
    # Step 1: 注入极端短句
    text = inject_micro_sentences(text, cfg['micro_sentence_density'])
    report['steps']['micro_sentences'] = True
    
    # Step 2: 调整段落方差
    text = adjust_paragraph_variance(text, cfg['paragraph_variance_ratio'])
    report['steps']['paragraph_variance'] = True
    
    # Step 3: 替换连接词
    text = replace_connectors(text, cfg['connector_replace_rate'])
    report['steps']['connector_replacement'] = True
    
    # Step 4: 对话碎片化
    text = fragment_dialogue(text, cfg['dialogue_fragmentation_rate'])
    report['steps']['dialogue_fragmentation'] = True
    
    # Step 5: 插入闲笔
    text = insert_digressions(text, cfg['digression_density'])
    report['steps']['digressions'] = True
    
    # Step 6: 注入不完美
    text = inject_minor_imperfections(text, cfg['imperfection_rate'])
    report['steps']['imperfections'] = True
    
    report['final_chars'] = count_chinese_chars(text)
    report['char_delta'] = report['final_chars'] - report['original_chars']
    report['char_delta_ratio'] = round(report['char_delta'] / max(report['original_chars'], 1), 4)
    
    return text, report


def main():
    if len(sys.argv) < 2:
        print("用法: python humanize.py <输入文件> [输出文件] [--strength low|medium|high]")
        print("说明: 对文本进行人类化后处理，制造'有人味的混乱'")
        sys.exit(1)
    
    input_file = Path(sys.argv[1])
    output_file = Path(sys.argv[2]) if len(sys.argv) > 2 and not sys.argv[2].startswith('--') else input_file.with_suffix('.humanized.txt')
    
    strength = 'medium'
    if '--strength' in sys.argv:
        idx = sys.argv.index('--strength')
        if idx + 1 < len(sys.argv):
            strength = sys.argv[idx + 1]
    
    text = read_text_safe(input_file)
    result_text, report = humanize(text, strength=strength)
    
    output_file.write_text(result_text, encoding='utf-8')
    
    report_file = output_file.with_suffix('.humanize.json')
    report_file.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    
    print(f"人类化处理完成：{output_file}")
    print(f"  原文：{report['original_chars']} 字")
    print(f"  处理后：{report['final_chars']} 字")
    print(f"  变化：{report['char_delta']:+d} 字（{report['char_delta_ratio']:+.2%}）")
    print(f"  处理步骤：{', '.join(report['steps'].keys())}")
    print(f"  报告：{report_file}")


if __name__ == '__main__':
    main()
