---
name: fiction-distiller
description: 小说风格全维度蒸馏 - 从任何小说文本中提取风格指纹，并以原汁原味的风格创作全新原创故事
---

完整指令见 @.opencode/skills/fiction-distiller/SKILL.md

本技能中 `@skill:knowledge/...` 引用指向 `.opencode/skills/fiction-distiller/knowledge/` 目录。映射规则：`@skill:knowledge/X/Y` → `knowledge/X/Y.md`（自动追加 `.md`），详见主指令的懒加载协议。

所有生成的内容统一保存到本文件同级的 `output/` 目录下，即 `.claude/skills/fiction-distiller/output/`。按类型和章节逐文件保存，一章一文件：

- `风格模型卡-《作品名》.md`
- `第01章-《故事名》.md`、`第02章-《故事名》.md`……
- `大纲-《故事名》.md`
- 短篇正文直接用 `《故事名》.md`
- 分析报告用 `分析-《作品名》.md`
