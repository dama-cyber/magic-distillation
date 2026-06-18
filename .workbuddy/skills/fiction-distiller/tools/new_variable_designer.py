"""
new_variable_designer.py
新变量方案设计工具
基于骨架卡和换元清单，生成新变量方案初稿
"""

import json
import sys
from pathlib import Path


def design_new_variables(variable_list, skeleton=None):
    """根据换元清单生成新变量方案"""
    
    # 按类型分组
    grouped = {}
    for v in variable_list.get('variables', []):
        t = v['type']
        if t not in grouped:
            grouped[t] = []
        grouped[t].append(v)
    
    # 自动生成新变量设计（基于简单映射）
    design = {
        '新变量方案': {
            '说明': '本方案为初稿，需要人工审核和创意调整',
            '主角': {},
            '场景': {},
            '情节框架': {},
            '道具与意象': [],
            '关系网络': [],
            '关键台词': [],
            '立意': {}
        }
    }
    
    # 人物映射：第一个识别到的人物作为主角
    persons = grouped.get('人物', [])
    if persons:
        design['新变量方案']['主角'] = {
            '原文姓名': persons[0]['original'],
            '新姓名': '待设计',
            '性别': '待设计',
            '年龄': '待设计',
            '职业': '待设计',
            '外貌': ['待设计'],
            '性格': ['待设计'],
            '目标': '待设计',
            '秘密': '待设计',
            '当前状态': '待设计'
        }
    
    # 地点映射：第一个地点作为主要场景
    locations = grouped.get('地点', [])
    if locations:
        design['新变量方案']['场景'] = {
            '原文地点': locations[0]['original'],
            '新地点': '待设计',
            '时代背景': '待设计',
            '自然环境': '待设计',
            '标志性空间': '待设计',
            '氛围基调': '待设计'
        }
    
    # 道具映射
    objects = grouped.get('道具/意象', [])
    for obj in objects[:5]:
        design['新变量方案']['道具与意象'].append({
            '原文': obj['original'],
            '新名称': '待设计',
            '功能': '待设计',
            '象征意义': '待设计'
        })
    
    # 台词映射
    dialogues = grouped.get('台词', [])
    for d in dialogues[:5]:
        design['新变量方案']['关键台词'].append({
            '原文台词': d['original'],
            '新台词': '待设计',
            '功能': '待设计'
        })
    
    # 情节框架
    design['新变量方案']['情节框架'] = {
        '触发事件': '待设计',
        '核心冲突': '待设计',
        '关键转折': '待设计',
        '高潮事件': '待设计',
        '结局事件': '待设计',
        '情绪曲线映射': '待设计'
    }
    
    # 立意
    design['新变量方案']['立意'] = {
        '主题类型': '待设计',
        '具体立意': '待设计',
        '结局导向': '待设计',
        '情感余韵': '待设计'
    }
    
    return design


def main():
    if len(sys.argv) < 2:
        print("用法: python new_variable_designer.py <换元清单.json> [骨架卡文件] [输出文件.json]")
        sys.exit(1)
    
    variable_file = Path(sys.argv[1])
    skeleton_file = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    output_file = Path(sys.argv[3]) if len(sys.argv) > 3 else variable_file.with_suffix('.design.json')
    
    variable_list = json.loads(variable_file.read_text(encoding='utf-8'))
    
    skeleton = None
    if skeleton_file and skeleton_file.exists():
        skeleton = skeleton_file.read_text(encoding='utf-8')
    
    design = design_new_variables(variable_list, skeleton)
    
    output_file.write_text(json.dumps(design, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"新变量方案初稿生成：{output_file}")
    print("请人工补充创意细节，确保功能等价、情绪等价、逻辑自洽")


if __name__ == '__main__':
    main()
