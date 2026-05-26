# M.A.M.A. Core

公众号全流程自动化 MCP Server —— Harness + Model = Agent

## 简介

M.A.M.A. Core 是一个基于 MCP（Model Context Protocol）构建的公众号全流程自动化平台。它将「热点抓取 → 文章生成 → 排版配图 → 安全检测 → 发布分发 → 数据分析 → 内容策略」整合为一个可被 AI 智能体直接调用的工具集。

## 特性

- **热点抓取**：双数据源 —— 公众号爆款 API + DailyHotApi 热榜聚合（30+ 平台）
- **文章生成**：4 种写作框架（清单/痛点/对比/叙事）× 5 种写作风格
- **标题引擎**：多维度规则评分（数字/悬念/痛点/情绪），10 个候选标题
- **图片生成**：DALL-E 3 / 通义万相双后端，封面 + 内文 + 分享卡片
- **排版适配**：容器语法（对话气泡/时间线/引用框/代码块）+ 排版主题
- **微信 SEO**：关键词密度分析 + 标题/首段关键词检查
- **安全检测**：基于 pyahocorasick 的敏感词引擎，广告法极限词 + 政治敏感词
- **数据分析**：账号画像 / 选题热力图 / 标题 A/B / 爆款模式 / 竞品对标 / 变现分析
- **内容策略**：综合推荐引擎，回答「下周该写什么」
- **多平台分发**：公众号 + 知乎/头条/百家号/CSDN（Wechatsync）
- **SKILL.md 工作流**：3 套强制工作流，保证输出质量

## 安装

### 方式一：本地开发模式（推荐）

```bash
git clone https://github.com/your-org/mamacore.git
cd mamacore
uv sync
```

### 方式二：全局安装

```bash
# 使用 uv 全局安装
uv tool install --from git+https://github.com/your-org/mamacore.git mamacore

# 或使用 pip 全局安装
pip install git+https://github.com/your-org/mamacore.git

# 验证安装
mama --help
mama-server --help
```

### 方式三：从源码安装

```bash
git clone https://github.com/your-org/mamacore.git
cd mamacore
pip install -e .   # 开发模式安装
```

### 复制示例配置

```bash
# 环境变量配置
cp .env.example .env
# 编辑 .env，填入你的 API Key

# MCP 配置（可选，Claude Code 自动发现）
cp .mcp.json.example .mcp.json
```

### 启动热榜服务（可选，用于 DailyHotApi 数据源）

```bash
# 方式一：一键启动
bash services/dailyhot/start.sh

# 方式二：手动启动
cd services/dailyhot && pnpm start

# 启动后访问: http://localhost:6688/weibo
```

## 配置

### 环境变量

完整配置示例见 `.env.example` 文件。复制后填入真实值：

```bash
cp .env.example .env
```

| 变量                       | 说明                         | 必填             |
| ------------------------ | -------------------------- | -------------- |
| `OPENAI_API_KEY`         | DALL-E 3 图片生成              | 需要配图时          |
| `DASHSCOPE_API_KEY`      | 通义万相图片生成                   | 需要配图时          |
| `MAMA_WECHAT_APP_ID`     | 公众号 AppID                  | 发布功能必填         |
| `MAMA_WECHAT_APP_SECRET` | 公众号 AppSecret              | 发布功能必填         |
| `MAMA_ACCOUNT_TYPE`      | 账号类型: service/personal     | 否（默认 personal） |
| `DAILYHOT_API_URL`       | DailyHotApi 服务地址            | 使用热榜功能时必填     |
| `MAMA_EXPORTER_URL`      | wechat-article-exporter 地址 | 否              |

### Claude Code 集成

项目根目录的 `.mcp.json` 已配置好 MCP Server。在 Claude Code 中自动发现，无需手动配置。

### OpenClaw 集成

```json
{
  "mcpServers": {
    "mamacore": {
      "command": "uv",
      "args": ["--directory", "/path/to/mamacore", "run", "src/mamacore/server.py"],
      "env": {
        "OPENAI_API_KEY": "sk-xxx",
        "MAMA_WECHAT_APP_ID": "xxx",
        "MAMA_WECHAT_APP_SECRET": "xxx"
      }
    }
  }
}
```

## 使用

### CLI 命令

```bash
# 查看今日热点
mama hot-today -s weibo -n 10

# 生成文章
mama write "AI Agent 开发" -f checklist -s satire -o article.md

# 排版转换
mama format article.md -t default -o article.html

# 敏感词检测
mama check article.md

# SEO 分析
mama seo article.md -k "AI Agent,智能体"

# 标题评分
mama score-title "关于 AI Agent，这 5 个建议你一定要知道"

# 数据分析
mama analyze -a my_account -d 30

# 发布草稿
mama publish article.html -t "文章标题"
```

### 独立运行模式 (Paseo 风格)

不依赖 Claude Code 宿主，通过 CLI 直接调度 Agent 完成全流程：

```bash
# 查看可用的 Agent Provider
mama providers

# 使用 Claude Code 驱动
mama run "写一篇关于 AI Agent 的文章" -p claude

# 指定框架和风格
mama run "写一篇关于职场成长的文章" -p claude -f pain -s experience

# 使用 OpenClaw 驱动
mama run "写一篇关于大模型的对比评测" -p openclaw -f compare

# 跳过确认
mama run "写一篇关于育儿经验的文章" -p claude -y

# 查看任务 / 连接日志 / 终止任务
mama ls
mama attach <task_id>
mama kill <task_id>
```

### Claude Code / MCP 工具

21 个 MCP Tools：

| 模块  | 工具                          | 说明                 |
| --- | --------------------------- | ------------------ |
| 热点  | `mama_hot_topics`           | 抓取全网热点             |
| 写作  | `mama_write_article`        | 全流程生成文章            |
| 写作  | `mama_generate_outline`     | 生成文章大纲             |
| 写作  | `mama_score_title`          | 标题评分               |
| 图片  | `mama_generate_images`      | 批量生成配图             |
| 图片  | `mama_generate_cover`       | 生成封面图              |
| 图片  | `mama_list_image_templates` | 列出图片模板             |
| 排版  | `mama_format_article`       | Markdown 转公众号 HTML |
| 排版  | `mama_list_themes`          | 列出排版主题             |
| 排版  | `mama_seo_check`            | 微信搜一搜 SEO 分析       |
| 数据  | `mama_analyze_account`      | 账号画像分析             |
| 数据  | `mama_import_metrics`       | CSV 导入历史数据         |
| 数据  | `mama_topic_heatmap`        | 选题热力图              |
| 数据  | `mama_content_strategy`     | 内容策略报告             |
| 数据  | `mama_competitor_gap`       | 竞品对标分析             |
| 安全  | `mama_check_sensitive`      | 敏感词检测              |
| 安全  | `mama_check_ad_law`         | 广告法合规检查            |
| 发布  | `mama_publish_draft`        | 发布到草稿箱             |
| 发布  | `mama_sync_to_platforms`    | 多平台同步              |
| 发布  | `mama_schedule_publish`     | 预约发布               |
| 系统  | `mama_health_check`         | 健康检查               |

### SKILL.md 工作流

在 Claude Code 中使用：

- `/wechat-article` — 公众号文章全流程（8 步）
- `/wechat-analytics` — 数据分析与内容策略（6 步）
- `/wechat-image` — 图片生成（3 步）

## 架构

```
mamacore/
├── src/mamacore/
│   ├── server.py              # MCP Server 入口 (FastMCP)
│   ├── cli.py                 # 独立 CLI 入口 (Typer)
│   ├── hot_topics/            # 热点抓取 (DailyHotApi)
│   ├── writer/                # 文章生成引擎
│   ├── image/                 # 图片生成 (DALL-E / 通义万相)
│   ├── adapter/               # 公众号排版适配器
│   ├── analytics/             # 数据分析与策略引擎
│   ├── safety/                # 敏感词检测 (pyahocorasick)
│   ├── publisher/             # 发布与多平台同步
│   └── config/                # 配置文件
├── .claude/skills/          # SKILL.md 工作流定义
├── data/                      # 数据目录 (SQLite + 导出文件)
├── .mcp.json                  # Claude Code MCP 配置
└── pyproject.toml             # 项目依赖
```

## 技术栈

- **MCP Server**: FastMCP (Python SDK)
- **数据模型**: Pydantic v2
- **HTTP 客户端**: httpx (异步)
- **敏感词引擎**: pyahocorasick (Aho-Corasick 自动机)
- **CLI**: Typer + Rich
- **配置**: PyYAML
- **数据存储**: SQLite
- **多平台分发**: Wechatsync CLI

## 支持的 Agent 和模型

### 支持的 AI 助手

| 类型        | 工具              | 说明                      |
| --------- | --------------- | ----------------------- |
| CLI Agent | Claude Code（推荐） | 完整支持 MCP + SKILL.md 双模式 |
| CLI Agent | Codex CLI       | 支持 MCP 工具调用             |
| CLI Agent | OpenClaw        | 支持 MCP 工具调用             |
| IDE Agent | Cursor          | 支持 SKILL.md 工作流         |
| IDE Agent | VS Code Copilot | 支持 SKILL.md 工作流         |

### 推荐模型

- **首选**：Claude Sonnet 4.6 / Claude Opus 4.7（Claude Code 默认模型）
- **备选**：GPT-4o / GPT-4o mini（通过 OpenAI API Key 接入）
- **不推荐**：GPT-3.5-turbo（内容质量和深度不足，生成的文章缺乏专业感）

### 模型降级说明

如果使用较小的模型（如 GPT-4o mini），以下能力会下降：

- 文章深度：内容趋于表面，缺乏洞察
- 框架遵循度：可能偏离清单型/痛点型的结构约束
- 标题质量：标题评分规则的参考意义下降
- 数据分析：对复杂数据的理解和建议质量降低

**建议**：写作和分析场景至少使用 Sonnet 级别以上的模型。

## 常见问题

### Q: 如何获取公众号 AppID 和 AppSecret？

A: 登录微信公众平台 → 设置与开发 → 开发 → 基本配置。注意：个人订阅号权限受限，2025年7月后无法通过 API 自动发布，只能创建草稿。

### Q: DailyHotApi 怎么部署？

A: 推荐使用 Docker 部署：`docker run -d -p 6688:6688 imsyy/dailyhot-api`。部署后设置 `DAILYHOT_API_URL=http://localhost:6688`。公共实例目前已不可用，必须自行部署。GitHub: https://github.com/imsyy/DailyHotApi

### Q: 图片生成需要哪些 API Key？

A: 二选一即可。DALL-E 3 需要 `OPENAI_API_KEY`，通义万相需要 `DASHSCOPE_API_KEY`。默认使用 DALL-E 3。

### Q: wechat-article-exporter 怎么用？

A: 推荐使用 Docker 部署：`docker compose up -d`（参考 https://github.com/wechat-article/wechat-article-exporter）。部署后设置 `MAMA_EXPORTER_URL=http://localhost:3000`。也可以手动导入 CSV 数据。

### Q: 没有 API Key 能用吗？

A: 可以。不设置 LLM 相关的 Key 时，文章生成和图片生成会返回模拟数据，其他功能（排版、敏感词检测、SEO 分析）不受影响。

### Q: 个人号能自动发布吗？

A: 不能。2025年7月后个人订阅号只能创建草稿，需要手动在公众号后台点击发布。已认证服务号可以自动发布。

## 开发

```bash
# 安装开发依赖
uv sync --all-extras

# 运行 MCP Server
uv run src/mamacore/server.py

# 运行 CLI
uv run mama --help
```

## 许可证

MIT
