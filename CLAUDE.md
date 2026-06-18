# fiction-distiller

稗官风骨全维蒸馏之器——自诸说部文字中提取格调之印，存其本味，别撰新篇。

## 自动发现

本仓库包含一个 `fiction-distiller` 技能，由两个平台共享同一套知识库：

- **opencode**: `.opencode/skills/fiction-distiller/SKILL.md`
- **Claude Code**: `.claude/skills/fiction-distiller/SKILL.md`

详细指令见 `.opencode/skills/fiction-distiller/SKILL.md`。知识文件位于 `.opencode/skills/fiction-distiller/knowledge/`，映射规则：`@skill:knowledge/X/Y` → `knowledge/X/Y.md`。采用四步懒加载协议（索引→基础层→体裁层→方法层），严格按步骤触发，禁止一次全加载。

生成的内容保存到各平台自己的 `output/` 目录，一章一文件。

## 使用方式

在对话中提供小说文本即可。系统自动判断篇幅、选择知识路径、执行蒸馏到创作的完整 pipeline。
