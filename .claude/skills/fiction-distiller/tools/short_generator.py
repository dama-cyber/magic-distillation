"""
short_generator.py
短篇生成工作流集成工具
调用 LLM 按骨架逐段生成新短篇
"""

import json
import sys
from pathlib import Path


def load_prompt(prompt_name, prompts_dir):
    """加载 prompt 文件"""
    prompt_file = prompts_dir / f'{prompt_name}.md'
    if prompt_file.exists():
        return prompt_file.read_text(encoding='utf-8')
    return None


def generate_paragraph_prompt(paragraph_info, skeleton, new_variables, budget, prompt_template):
    """生成单段生成的 prompt"""
    prompt = prompt_template
    
    # 替换占位符
    prompt = prompt.replace('[段落编号]', str(paragraph_info['index']))
    prompt = prompt.replace('[段落功能]', paragraph_info.get('function', '待生成'))
    prompt = prompt.replace('[Y]', str(paragraph_info.get('target_chars', 200)))
    prompt = prompt.replace('[主导情绪]', paragraph_info.get('emotion', '待生成'))
    prompt = prompt.replace('[Z%]', str(int(paragraph_info.get('dialogue_ratio', 0) * 100)))
    
    # 插入骨架卡摘要
    skeleton_summary = json.dumps(skeleton, ensure_ascii=False, indent=2)
    prompt = prompt.replace('[在此处插入新变量方案中的关键信息]', skeleton_summary[:500])
    
    return prompt


def main():
    if len(sys.argv) < 4:
        print("用法: python short_generator.py <骨架卡.yaml> <新变量方案.json> <字数预算.json>")
        print("说明：本工具生成各段 prompt，需要配合 LLM 使用")
        sys.exit(1)
    
    skeleton_file = Path(sys.argv[1])
    design_file = Path(sys.argv[2])
    budget_file = Path(sys.argv[3])
    
    prompts_dir = Path(__file__).parent.parent / 'prompts'
    prompt_template = load_prompt('p04-paragraph-generate', prompts_dir)
    
    if not prompt_template:
        print(f"错误：找不到 prompt 文件 {prompts_dir / 'p04-paragraph-generate.md'}")
        sys.exit(1)
    
    skeleton = skeleton_file.read_text(encoding='utf-8')
    design = json.loads(design_file.read_text(encoding='utf-8'))
    budget = json.loads(budget_file.read_text(encoding='utf-8'))
    
    # 生成每个段落的 prompt
    output_dir = Path('generated_prompts')
    output_dir.mkdir(exist_ok=True)
    
    for para in budget.get('paragraphs', []):
        para_info = {
            'index': para['index'],
            'function': '待生成',  # 应从骨架卡提取
            'target_chars': para['target_chars'],
            'emotion': '待生成',
            'dialogue_ratio': para['dialogue_ratio']
        }
        
        prompt = generate_paragraph_prompt(para_info, skeleton, design, budget, prompt_template)
        output_file = output_dir / f'paragraph_{para["index"]:02d}_prompt.md'
        output_file.write_text(prompt, encoding='utf-8')
    
    print(f"已生成 {len(budget.get('paragraphs', []))} 个段落 prompt：{output_dir}")
    print("请逐段将这些 prompt 提交给 LLM，获取生成的段落内容")


if __name__ == '__main__':
    main()
