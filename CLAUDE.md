# CLAUDE.md — M.A.M.A. Core 项目级 AI 指令

## 项目定位

M.A.M.A. Core 是公众号全流程自动化平台，实现 **Harness + Model = Agent** 架构理念。
用户用自然语言即可完成公众号运营全链路：热点发现 → 文章创作 → 排版配图 → 安全审核 → 发布分发 → 数据分析 → 内容策略。

## 双模式运行

本项目同时支持两种模式，叠加使用效果最佳：

### 模式一：MCP Server（工具层）

通过 `.mcp.json` 注册为 MCP Server，提供 **21 个 MCP Tools**。
用户在对话中描述需求时，Claude Code 自动选择并调用对应工具。

### 模式二：SKILL.md（工作流层）

通过 `.claude/skills/*/SKILL.md` 注册为 Claude Code 技能，提供 **3 套强制工作流**：

| 技能 | 触发词 | 作用 |
|------|--------|------|
| `/wechat-article` | 写公众号、写推文、公众号文章、微信推文 | 8 步全流程：热点→选题→框架→写作→标题→配图→排版→安全→发布 |
| `/wechat-analytics` | 看看文章数据、效果复盘、内容策略、数据分析 | 6 步分析流程：采集→指标→热力图→爆款模式→策略→竞品 |
| `/wechat-image` | 生成封面、生成配图、做张封面 | 3 步图片生成：选模板→生成→展示 |

**使用建议**：用户说"写一篇关于 X 的公众号文章"时，触发 `/wechat-article`；
用户说"帮我看看数据"时，触发 `/wechat-analytics`。

## MCP Tools 索引

### 热点
- `mama_hot_topics` — 查询公众号爆款文章（低粉高阅读/阅读靠前/原创/数据增长）

### 写作
- `mama_write_article` — 全流程生成文章（大纲+初稿+增强+标题候选）
- `mama_generate_outline` — 仅生成大纲
- `mama_score_title` — 标题评分（数字/悬念/痛点/情绪四维打分）

### 图片
- `mama_generate_images` — 批量生成配图（封面+内文）
- `mama_generate_cover` — 单独生成封面图
- `mama_list_image_templates` — 列出可用的图片提示词模板

### 排版
- `mama_format_article` — Markdown → 公众号 HTML（支持容器语法）
- `mama_list_themes` — 列出排版主题
- `mama_seo_check` — 微信搜一搜 SEO 分析

### 数据
- `mama_analyze_account` — 账号画像分析（阅读/点赞/互动率/最佳发文时间）
- `mama_import_metrics` — CSV 导入历史数据
- `mama_topic_heatmap` — 选题热力图（什么话题火）
- `mama_content_strategy` — 内容策略报告（回答"下周该写什么"）
- `mama_competitor_gap` — 竞品对标分析

### 安全
- `mama_check_sensitive` — 敏感词检测（广告法+政治+平台特定）
- `mama_check_ad_law` — 广告法极限词专项检测

### 发布
- `mama_publish_draft` — 发布到公众号草稿箱
- `mama_sync_to_platforms` — 多平台同步（知乎/头条/百家号/CSDN）
- `mama_schedule_publish` — 预约发布

### 系统
- `mama_health_check` — 健康检查，列出可用模块

## 写作框架选择指南

根据选题类型自动推荐框架：

| 选题类型 | 推荐框架 | 示例 |
|----------|----------|------|
| 攻略/指南/盘点 | checklist（清单型） | "2026 年 AI 工具 Top 10" |
| 焦虑/困惑/误区 | pain（痛点型） | "为什么你的 AI 工具总是用不好？" |
| 选型/评测/对比 | compare（对比型） | "Claude vs GPT-4o：开发者选型指南" |
| 经历分享/故事 | narrative（叙事型） | "我做 AI 应用这半年：3 个教训" |

## 容器语法

在 Markdown 中使用以下容器，排版时自动转为 HTML：

```
:::dialogue ... :::end        → 对话气泡
:::timeline ... :::end         → 时间线
:::callout variant=info ... :::end  → 引用框（info/warning/success/tip）
:::code language=python ... :::end  → 代码块
```

## 发布注意事项

- **个人订阅号**（2025年7月后）：只能创建草稿，需用户在公众号后台手动点击发布
- **已认证服务号**：支持自动发布（设置 `MAMA_ACCOUNT_TYPE=service`）
- 发布前**必须**经过 `mama_check_sensitive` 安全检测
- 检测未通过时，必须告知用户具体问题词和建议，**阻止发布**

## 环境变量

| 变量 | 用途 | 必填 |
|------|------|------|
| `OPENAI_API_KEY` | DALL-E 3 图片生成 | 需要配图时 |
| `DASHSCOPE_API_KEY` | 通义万相图片生成 | 需要配图时 |
| `MAMA_WECHAT_APP_ID` | 公众号 AppID | 发布功能 |
| `MAMA_WECHAT_APP_SECRET` | 公众号 AppSecret | 发布功能 |
| `MAMA_ACCOUNT_TYPE` | `service` 或 `personal` | 否（默认 personal） |
| `MAMA_EXPORTER_URL` | wechat-article-exporter 地址 | 否 |

## 开发约定

- 使用 `uv` 管理依赖
- 中文文案规范：中英文之间加空格，中文与数字之间加空格
- MCP 走 stdio 通信，**禁止 print 到 stdout**（用 stderr）
- 新增 MCP tool 必须在对应模块的 `register_tools()` 中注册，并写好 docstring
- 敏感词库新增词条后需重启 server（Aho-Corasick 自动机在启动时构建）

## 文件结构速查

```
src/mamacore/
├── server.py              # MCP Server 入口 (FastMCP)
├── cli.py                 # 独立 CLI (Typer, 8 个命令)
├── hot_topics/            # 热点抓取 (gzh.litpp.com 公众号爆款 API)
├── writer/                # 文章生成 (4框架×5风格 + 标题引擎)
├── image/                 # 图片生成 (DALL-E / 通义万相双后端)
├── adapter/               # 排版适配 (容器语法 + 主题 + SEO)
├── analytics/             # 数据分析 (采集/指标/热力图/A/B/爆款/竞品/变现/策略)
├── safety/                # 敏感词检测 (pyahocorasick 自动机)
├── publisher/             # 发布 (公众号 API + Wechatsync 多平台)
└── config/                # 配置 (style/platform/images/themes)
```
