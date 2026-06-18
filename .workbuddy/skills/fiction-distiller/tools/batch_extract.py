"""
batch_extract.py v2.0
批量骨架提取工具 —— 纯结构指纹，不含任何原文信息

命名规则（零内容、纯结构）:
    {序号4位}_{题材}_{字数K}_{开头类型}_{段落数段}_{对话%}.yaml

示例:
    0001_复仇逆袭_8K_悬念开篇_7段_31%.yaml
    0042_穿越重生_5K_直叙开篇_12段_18%.yaml
    1050_虐恋言情_3K_回忆开篇_4段_45%.yaml

安全原则:
    - 文件名不含任何故事关键词
    - 骨架内容不含人物名、地名、具体台词
    - 段落首句替换为长度+类型的元数据
"""

import os
import re
import json
import sys
from pathlib import Path


# =============== 编码检测 ===============

def read_text_safe(filepath):
    with open(filepath, 'rb') as f:
        raw = f.read()
    try:
        return raw.decode('utf-8-sig')
    except UnicodeDecodeError:
        try:
            return raw.decode('gbk', errors='replace')
        except:
            return raw.decode('utf-8', errors='replace')


# =============== 题材分类 ===============

GENRE_KEYWORDS = {
    '穿越重生': ['穿越', '重生', '前世', '回到过去', '时光倒流', '重新来过', '穿到', '穿越到', '回到了'],
    '复仇逆袭': ['复仇', '报复', '打脸', '逆袭', '翻身', '报应', '求我原谅', '求我回来', '当初看不起', '悔疯'],
    '虐恋言情': ['老公', '出轨', '离婚', '小三', '白月光', '替身', '前任', '婚约', '怀孕', '产检'],
    '婆媳家庭': ['婆婆', '媳妇', '嫂子', '丈母娘', '婆家', '娘家', '小姑子', '大姑子', '妯娌'],
    '校园青春': ['高考', '学校', '同桌', '老师', '同学', '宿舍', '大学', '毕业', '考研'],
    '都市生活': ['拆迁', '买房', '存款', '工资', '加班', '辞职', '创业', '公司', '老板', '房租'],
    '亲情伦理': ['妈妈', '爸爸', '女儿', '儿子', '父亲', '母亲', '抚养', '养育', '养大', '照顾', '瘫痪', '送给'],
    '悬疑惊悚': ['死', '杀', '尸体', '坟', '鬼', '失踪', '警察', '凶手', '监控', '密码'],
    '系统金手指': ['系统', '绑定', '奖励', '技能', '升级', '金手指'],
    '豪门世家': ['总裁', '豪门', '亿万', '首富', '少爷', '千金', '继承', '家产'],
}


def classify_genre(text, first_paragraph):
    combined = (first_paragraph + ' ' + text[:3000]).lower()
    scores = {}
    for genre, keywords in GENRE_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw.lower() in combined)
        if score > 0:
            scores[genre] = score
    if not scores:
        return ['网文短篇']
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [g for g, s in ranked[:2] if s >= 2] or [ranked[0][0]]


# =============== 开头类型 ===============

def classify_opening(first_paragraph):
    fp = first_paragraph[:200]
    
    if re.search(r'["""""][^"""""]{2,30}["""""]', fp):
        return '对话切入'
    
    conflict_words = ['那天', '突然', '却', '不料', '没想到', '谁知', '结果', '居然', '竟然']
    if any(w in fp[:80] for w in conflict_words):
        return '悬念开篇'
    
    time_words = ['那年', '记得', '小时候', '冬天', '夏天', '秋天', '春天', '早上', '晚上', '凌晨']
    if any(w in fp[:50] for w in time_words):
        return '回忆开篇'
    
    return '直叙开篇'


# =============== 字数分级 ===============

def classify_length(chars):
    if chars < 2000:
        return ('极短', '2K', '极短')
    elif chars < 4000:
        return ('短篇', '3K', '短篇')
    elif chars < 6000:
        return ('中短', '5K', '中短')
    elif chars < 10000:
        return ('中篇', '8K', '中篇')
    elif chars < 20000:
        return ('长篇', '15K', '长篇')
    else:
        k = chars // 1000
        return ('超长', f'{k}K', '超长')


# =============== 文本清洗 ===============

BOILERPLATE_PATTERNS = [
    r'【全文完】',
    r'本作品来源网络.*',
    r'内容版权归作者所有.*',
    r'观看后请在24小时内删除.*',
    r'如果侵犯了您的权益.*',
    r'如果有能力请支持正版.*',
    r'来自盐选专栏.*',
    r'盐选.*',
    r'[（(]全文完[)）]',
    r'——全文完——',
    r'^[#\s]*$',
]

BOILERPLATE_TITLES = [
    '完结短篇', '短篇', '完结', '全文完', '完整版',
    '盐选', '知乎盐选', '知乎', '专栏',
    'short story', 'story', '短篇故事',
]


def is_boilerplate(line):
    stripped = line.strip()
    if not stripped:
        return False
    
    # 匹配boilerplate模式
    for pattern in BOILERPLATE_PATTERNS:
        if re.match(pattern, stripped):
            return True
    
    # 纯数字/符号/英文字母组成的行
    if re.match(r'^[\d\W_a-zA-Z]+$', stripped):
        return True
    
    # 超短行且含"全文"/"完"
    if len(stripped) < 15 and ('全文' in stripped or '完' in stripped or '版权' in stripped):
        return True
    
    return False


def clean_text(text):
    """移除版权声明、完结标记等boilerplate"""
    lines = text.split('\n')
    filtered = [l for l in lines if not is_boilerplate(l)]
    return '\n'.join(filtered)


def is_boilerplate_filename(name):
    for bt in BOILERPLATE_TITLES:
        if bt in name:
            return True
    # 纯数字文件名
    if re.match(r'^[\d\-_\.]+$', name):
        return True
    return False


# =============== 文本分析 ===============

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


def classify_para_function(para, idx, total):
    """判断段落功能"""
    chars = count_chinese_chars(para)
    if idx == 0:
        return '开头'
    if idx == total - 1:
        return '结尾'
    
    # 对话段落 —— 支持多种引号
    d_chars = 0
    for pattern in [r'[""""]([^""""]+)[""""]', r'[""]([^""]+)[""]', r'[「]([^」]+)[」]', r'[『]([^』]+)[』]']:
        d_chars += sum(count_chinese_chars(m.group(1)) for m in re.finditer(pattern, para))
    if d_chars > chars * 0.4:
        return '对话段'
    
    # 转折/高潮段落
    if any(w in para for w in ['突然', '不料', '谁知', '然而', '竟然', '猛地', '刹那间']):
        return '转折段'
    
    if idx < total // 3:
        return '铺垫段'
    if idx < total * 2 // 3:
        return '发展段'
    return '收束段'


# =============== 骨架提取 ===============

def extract_skeleton(text):
    """提取纯结构骨架，不含原文内容"""
    paragraphs = split_paragraphs(text)
    sentences = split_sentences(text)
    total_chars = count_chinese_chars(text)
    
    if total_chars < 200 or len(paragraphs) < 2:
        return None
    
    # 过滤合集/目录/长篇
    if len(paragraphs) > 200:
        return None
    avg_para_len = total_chars / len(paragraphs)
    if avg_para_len < 30:
        return None
    if total_chars > 50000:
        return None  # 超过5万字，非短篇
    
    para_lengths = [count_chinese_chars(p) for p in paragraphs]
    
    sent_lengths = [count_chinese_chars(s) for s in sentences]
    sent_mean = sum(sent_lengths) / len(sent_lengths) if sent_lengths else 0
    
    if sent_lengths:
        short_count = sum(1 for l in sent_lengths if l <= 10)
        medium_count = sum(1 for l in sent_lengths if 10 < l <= 25)
        long_count = sum(1 for l in sent_lengths if l > 25)
        total_sents = len(sent_lengths)
        short_ratio = round(short_count / total_sents * 100)
        medium_ratio = round(medium_count / total_sents * 100)
        long_ratio = round(long_count / total_sents * 100)
    else:
        short_ratio = medium_ratio = long_ratio = 0
    
    # 对话比例 —— 支持多种引号格式
    all_dialogue_chars = 0
    for pattern in [r'[""""]([^""""]+)[""""]', r'[""]([^""]+)[""]', r'[「]([^」]+)[」]', r'[『]([^』]+)[』]']:
        all_dialogue_chars += sum(count_chinese_chars(match.group(1)) for match in re.finditer(pattern, text))
    dialogue_ratio = round(all_dialogue_chars / total_chars * 100) if total_chars > 0 else 0
    
    # 段落结构 —— 不含原文首句，只用元数据描述
    para_structure = []
    total = len(paragraphs)
    for i, p in enumerate(paragraphs):
        chars = count_chinese_chars(p)
        func = classify_para_function(p, i, total)
        
        # 段落长度级别
        if chars < 50:
            level = '极短'
        elif chars < 200:
            level = '短'
        elif chars < 500:
            level = '中'
        elif chars < 1500:
            level = '长'
        else:
            level = '极长'
        
        # 是否含对话
        has_dialogue = bool(re.search(r'["""""]', p))
        has_dialogue_char = '含对话' if has_dialogue else '纯叙述'
        
        para_structure.append({
            '段': i + 1,
            '字数': chars,
            '长度级': level,
            '功能': func,
            '类型': has_dialogue_char,
        })
    
    # 计算段落长度方差比
    if len(para_lengths) >= 2:
        max_len = max(para_lengths)
        min_len = min(l for l in para_lengths if l > 0)
        variance_ratio = round(max_len / min_len, 1) if min_len > 0 else 1.0
    else:
        variance_ratio = 1.0
    
    return {
        '总字数': total_chars,
        '段落数': len(paragraphs),
        '句子数': len(sentences),
        '段落方差比': variance_ratio,
        '平均段长': round(sum(para_lengths) / len(para_lengths)),
        '平均句长': round(sent_mean, 1),
        '短句比例': f'{short_ratio}%',
        '中句比例': f'{medium_ratio}%',
        '长句比例': f'{long_ratio}%',
        '对话比例': f'{dialogue_ratio}%',
        '段落结构': para_structure,
    }


# =============== 文件名生成（纯结构、零内容） ===============

def generate_filename(index, genre, length_tier, opening, para_count, dialogue_pct):
    """
    {序号4位}_{题材}_{字数K}_{开头类型}_{段落数段}_{对话%}.yaml
    不含任何故事关键词
    """
    genre_tag = genre[0].replace(' ', '_') if genre else '未分类'
    return f"{index:04d}_{genre_tag}_{length_tier}_{opening}_{para_count}段_{dialogue_pct}%"


# =============== YAML 输出 ===============

def skeleton_to_yaml(index, genre, length_label, opening, para_count, dialogue_pct, skeleton):
    """骨架数据 → 纯元数据YAML"""
    lines = [
        f"# 骨架指纹 {index:04d}",
        f"版本: '2.0'",
        f"题材: {genre}",
        f"字数等级: '{length_label}'",
        f"开头类型: '{opening}'",
        f"段落数: {para_count}",
        f"对话占比: '{dialogue_pct}%'",
        f"",
        f"骨架卡:",
        f"  总字数: {skeleton['总字数']}",
        f"  段落数: {skeleton['段落数']}",
        f"  句子数: {skeleton['句子数']}",
        f"  段落方差比: {skeleton['段落方差比']}",
        f"  平均段长: {skeleton['平均段长']}",
        f"  平均句长: {skeleton['平均句长']}",
        f"  短句比例: '{skeleton['短句比例']}'",
        f"  中句比例: '{skeleton['中句比例']}'",
        f"  长句比例: '{skeleton['长句比例']}'",
        f"  对话比例: '{skeleton['对话比例']}'",
        f"  段落结构:",
    ]
    
    for para in skeleton['段落结构']:
        lines.append(f"    - 段: {para['段']}")
        lines.append(f"      字数: {para['字数']}")
        lines.append(f"      长度级: {para['长度级']}")
        lines.append(f"      功能: {para['功能']}")
        lines.append(f"      类型: {para['类型']}")
    
    lines.append(f"")
    lines.append(f"  # 以下需 LLM 填充")
    lines.append(f"  写法规则:")
    lines.append(f"    开头: '待 LLM 判断'")
    lines.append(f"    中段: '待 LLM 判断'")
    lines.append(f"    结尾: '待 LLM 判断'")
    lines.append(f"    视角: '待 LLM 判断'")
    lines.append(f"  情绪曲线: '待 LLM 标注'")
    
    return '\n'.join(lines)


# =============== 主流程 ===============

def process_directory(input_dir, output_dir=None):
    input_path = Path(input_dir)
    if not input_path.exists():
        print(f"错误：目录不存在 {input_path}")
        return None
    
    if output_dir is None:
        output_dir = Path(__file__).parent.parent / 'skeleton_library'
    else:
        output_dir = Path(output_dir)
    
    # 清空旧骨架
    skeletons_dir = output_dir / 'skeletons'
    if skeletons_dir.exists():
        for f in skeletons_dir.iterdir():
            f.unlink()
    skeletons_dir.mkdir(parents=True, exist_ok=True)
    
    files = list(input_path.rglob('*.txt'))
    print(f"找到 {len(files)} 个 .txt 文件")
    print(f"输出目录：{output_dir}")
    print()
    
    catalog = []
    stats = {
        'total_files': len(files),
        'processed': 0,
        'skipped_too_short': 0,
        'skipped_boilerplate_title': 0,
        'skipped_read_error': 0,
        'genre_distribution': {},
        'length_distribution': {},
        'opening_distribution': {},
    }
    
    index = 0
    
    for filepath in sorted(files):
        try:
            text = read_text_safe(str(filepath))
            
            # 清洗boilerplate
            text = clean_text(text)
            total_chars = count_chinese_chars(text)
            
            if total_chars < 200:
                stats['skipped_too_short'] += 1
                continue
            
            # 提取骨架
            skeleton = extract_skeleton(text)
            if skeleton is None:
                stats['skipped_too_short'] += 1
                continue
            
            # 第一段用于题材/开头分类
            paragraphs = split_paragraphs(text)
            first_para = paragraphs[0][:300] if paragraphs else ''
            
            # 分类
            genres = classify_genre(text, first_para)
            opening = classify_opening(first_para)
            length_label_raw, length_tier, length_label = classify_length(total_chars)
            para_count = len(paragraphs)
            dialogue_pct = int(skeleton.get('对话比例', '0%').rstrip('%'))
            
            # 生成纯结构文件名
            filename = generate_filename(index, genres, length_tier, opening, para_count, dialogue_pct)
            
            # 保存骨架
            output_path = skeletons_dir / f"{filename}.yaml"
            yaml_content = skeleton_to_yaml(index, genres, length_label_raw, opening, para_count, dialogue_pct, skeleton)
            output_path.write_text(yaml_content, encoding='utf-8')
            
            # 更新统计
            stats['processed'] += 1
            for g in genres:
                stats['genre_distribution'][g] = stats['genre_distribution'].get(g, 0) + 1
            stats['length_distribution'][length_label] = stats['length_distribution'].get(length_label, 0) + 1
            stats['opening_distribution'][opening] = stats['opening_distribution'].get(opening, 0) + 1
            
            catalog.append({
                'index': index,
                'file': filename,
                'genre': genres,
                'length': length_label,
                'chars': total_chars,
                'opening': opening,
                'paragraphs': para_count,
                'dialogue_pct': dialogue_pct,
                'short_ratio': skeleton['短句比例'],
                'long_ratio': skeleton['长句比例'],
                'variance_ratio': skeleton['段落方差比'],
            })
            
            index += 1
            
            if index % 200 == 0:
                print(f"  已处理 {index} 个...")
        
        except Exception as e:
            stats['skipped_read_error'] += 1
            if stats['skipped_read_error'] <= 5:
                print(f"  跳过 {filepath.name}: {e}")
    
    # 保存目录
    (output_dir / 'catalog.json').write_text(
        json.dumps({'total': len(catalog), 'entries': catalog}, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )
    
    # 保存统计
    (output_dir / 'stats.json').write_text(
        json.dumps(stats, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )
    
    print()
    print(f"完成！")
    print(f"  处理: {stats['processed']} 个")
    print(f"  跳过(太短): {stats['skipped_too_short']} 个")
    print(f"  跳过(错误): {stats['skipped_read_error']} 个")
    print(f"  输出目录: {output_dir}")
    
    return catalog


def main():
    if len(sys.argv) < 2:
        print("用法: python batch_extract.py <小说文件夹路径> [输出目录]")
        print("命名规则: {序号}_{题材}_{字数K}_{开头类型}_{段落数段}_{对话%}.yaml")
        print("安全原则: 纯结构指纹，不含任何原文内容")
        sys.exit(1)
    
    input_dir = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    process_directory(input_dir, output_dir)


if __name__ == '__main__':
    main()
