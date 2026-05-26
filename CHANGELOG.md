# 更新日志

所有重要的项目变更都将记录在此文件中。

## [0.1.0] — 2026-05-25

### 新增
- MCP Server 基础框架（FastMCP，21 个 Tools）
- 热点抓取模块（DailyHotApi，30+ 中国平台）
- 文章生成引擎（4 框架 × 5 风格 + 标题评分引擎）
- 图片生成层（DALL-E 3 / 通义万相双后端，真实 API 调用）
- 公众号排版适配器（容器语法 + 排版主题 + SEO 分析）
- 数据分析模块（采集/指标/热力图/A-B/爆款模式/竞品对标/变现分析）
- 内容策略推荐引擎（回答"下周该写什么"）
- 敏感词检测引擎（pyahocorasick Aho-Corasick 自动机 + 广告法词库）
- 发布与多平台同步（公众号 API + Wechatsync）
- CLI 独立入口（8 个命令）
- LLM 客户端（指数退避重试 + 流式输出 + Token 成本估算）
- 热点数据缓存（10 分钟 TTL + 60 次/分钟限流）
- 微信 API Token 缓存（7200s TTL + 自动刷新）
- SQLite Schema 版本化迁移
- 3 套 SKILL.md 强制工作流（含门控/BLOCKING/spec_lock/角色切换/禁止规则）
- Plugin 分发配置（.claude-plugin/marketplace.json）
- CLAUDE.md 项目级 AI 指令
- 2 个端到端示例（清单型 + 痛点型文章）

### 技术栈
- FastMCP / Pydantic v2 / httpx / pyahocorasick / Typer / OpenAI SDK / SQLite
