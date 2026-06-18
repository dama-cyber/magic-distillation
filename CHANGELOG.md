# Changelog

## [4.1.0] - 2026-06-18

### Added
- ✅ **统一质量报告工具**：新增 `quality_report.py`，集成字数/原创性/反检测三维度检查，输出 JSON + HTML 可视化报告
- ✅ **Prompt v4.1 全面重写**：
  - `p02-variable-annotate.md`：增加影响层级标注、同义替换禁忌清单、原文危险片段提取
  - `p03-new-variable-design.md`：零残留标准从8字提至4字，禁止近义变体，增加反检测约束
  - `p04-paragraph-generate.md`：彻底重写为"功能等价重写"模式，增加4字禁止硬约束，正确/错误示例对比
  - `p05-humanize.md`：增加原文危险片段扫描步骤，AI特征词分级黑名单（硬/软），节奏指标硬约束
  - `p06-word-count-fix.md`：扩写时增加原创性约束，禁止引入原文片段
  - `p07-self-check.md`：增加同义替换禁忌扫描、句式残留检测、分级优先级

### Changed
- ✅ **originality_checker.py v2.0**：
  - 三级残留检测：真实变量残留 / 7字+潜在残留 / 4-6字日常短语（高误报率，单独统计）
  - 常见中文短语白名单，减少4-6字误报
  - 8-gram阈值从0放宽至10（更合理）
  - LCS增加位置定位和上下文提取
  - 新增段落级原创性分析（标记高风险段落）
  - 新增同义替换禁忌扫描
  - 新增N-gram分类（常见短语 vs 独特重叠）
- ✅ **anti_detection_checker.py v2.0**：
  - AI特征词黑名单分硬/软两级：硬黑名单命中=失败，软黑名单阈值≤5次
  - 模式化标记分硬/软：硬模式化命中=失败，软模式化阈值≤3
  - 日常高频词（又、仿佛、一样、重要的等）从黑名单移除
  - 新增短句占比（≥15%）和长短句交替率（≥10%）指标
  - 新增段落级突发性分析
  - 每个命中提供上下文片段
- ✅ **问题清单更新**：标记所有v4.0问题已在v4.1中修复，待重新测试验证
- ✅ **README.md 更新**：从v1.1风格蒸馏→v4.1短篇换元仿写，完整重写

### Fixed
- 🔧 修复核心问题：生成器从"换名微调"改为"功能等价重写"（p04全面重写）
- 🔧 修复工具误报：originality_checker 4-6字日常短语误报、anti_detection_checker 日常高频词误报
- 🔧 修复联动缺失：生成prompt嵌入原创性+反检测+字数三维联动约束

---

## [4.0.0] - 2026-06-18

### Added
- ✅ **短篇换元仿写核心**：七步工作流（分析→提取→标注→设计→生成→对齐→验证）
- ✅ **四层换元方法**：词句换元、片段换元、框架换元、立意换元
- ✅ **反检测技术栈**：困惑度/突发性检测、长短句交错、人味化注入、AI特征词黑名单
- ✅ **字数对齐系统**：段落级字数预算 ±5%，扩写/压缩技巧
- ✅ **原创性验证**：N-gram重合、变量残留、LCS检测、句子结构相似度
- ✅ **7个分离式Prompt**（p01-p07）
- ✅ **9个Python工具**（含 make_curated_vars.py）
- ✅ **4个新知识模块**：short-substitution/、anti-detection-short/、word-count-control/、originality-check/
- ✅ **3个新模板**：骨架卡、换元清单、验证报告
- ✅ **三平台同步**：opencode/claude/workbuddy 完整独立副本

---

## [1.1.0] - 2026-06-18

### Added
- ✅ **WorkBuddy 平台支持**：新增 `.workbuddy/skills/fiction-distiller/` 完整目录结构
- ✅ **输出模板系统**：新增 `templates/` 目录，包含 5 个标准化模板
  - `style-model-card.md` - 风格模型卡模板
  - `outline.md` - 故事大纲模板
  - `originality-statement.md` - 原创性声明模板
  - `short-story.md` - 短篇正文模板
  - `long-story-chapter.md` - 长篇章节模板
- ✅ **知识库元数据**：所有 32 个知识文件添加标准 YAML frontmatter
  - 包含 title, category, order, version, last_updated, related_files
- ✅ **批量处理脚本**：新增 `add_metadata.py` 用于批量添加元数据

### Changed
- ✅ **统一三平台格式**：
  - `.opencode/SKILL.md` - 保持原有格式
  - `.claude/SKILL.md` - 消除对 `.opencode` 的路径依赖，改为独立运行
  - `.workbuddy/SKILL.md` - 新增，符合 WorkBuddy 技能格式规范
- ✅ **知识库独立化**：
  - 每个平台拥有完整独立的 `knowledge/` 目录副本
  - 共 3 个平台 × 32 个文件 = 96 个知识文件
- ✅ **更新 README.md**：
  - 添加 WorkBuddy 支持说明
  - 更新项目结构图
  - 添加模板系统说明
  - 添加版本历史章节

### Fixed
- 修复 `.claude/SKILL.md` 依赖 `.opencode` 路径的问题
- 修复知识库文件缺少标准元数据的问题

### Technical Details
- **Files Modified**: 105 个（3 个 SKILL.md + 96 个知识文件 + README.md + 新增 6 个模板文件）
- **Files Created**: 8 个（3 个目录 + 5 个模板文件 + 1 个脚本）
- **Breaking Changes**: 无（向后兼容 v1.0.0）

---

## [1.0.0] - 2025-05-29

### Added
- ✅ 初始版本发布
- ✅ 支持 OpenCode 平台
- ✅ 支持 Claude Code 平台
- ✅ 32 个知识文件，覆盖 6 大知识模块
- ✅ 三层懒加载知识库架构
- ✅ 完整的风格蒸馏到创作工作流

---

**Legend**:
- ✅ Added - 新功能
- ✅ Changed - 功能变更
- ✅ Deprecated - 即将废弃的功能
- ✅ Removed - 已移除的功能
- ✅ Fixed - Bug 修复
- ✅ Security - 安全问题修复
