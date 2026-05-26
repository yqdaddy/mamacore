# DailyHot Skill

<div align="center">

**聚合 56+ 中文平台热榜数据 · 一条命令获取全网热点**

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Node](https://img.shields.io/badge/Node-%3E%3D20-green.svg)](https://nodejs.org/)
[![Skill](https://img.shields.io/badge/Claude_Code-Skill-orange.svg)](https://code.claude.com/docs/en/skills)

</div>

---

## 是什么？

DailyHot Skill 是一个 Claude Code 技能扩展，底层调用 [DailyHot API](https://github.com/imsyy/DailyHotApi)，聚合 56+ 中文内容平台的实时热榜数据。

```
┌─────────────────────────────────────────────────────────────┐
│                    Claude Code 会话                          │
│                                                             │
│   你: "看看今天的热点，帮我汇总到一起"                          │
│         ↓                                                   │
│   ┌─────────────────────────────────────────────────────┐   │
│   │           dailyhot-skill 自动触发                    │   │
│   │                                                     │   │
│   │  并行查询 → 36氪 · IT之家 · 知乎 · B站 · 少数派      │   │
│   │  关键词筛选 → 按 AI/科技 过滤                         │   │
│   │  合并汇总 → 结构化热点报告                            │   │
│   └─────────────────────────────────────────────────────┘   │
│         ↓                                                   │
│   📋 今日科技热点汇总                                        │
│   ┌──────────────────────────────────────┐                 │
│   │ 【36氪】 1. GPT-5 发布，多模态能力... │                 │
│   │ 【知乎】 2. 如何看待最新的大模型...   │                 │
│   │ 【IT之家】 3. 英伟达发布新一代GPU...  │                 │
│   │ 【B站】  4. AI编程工具实测，效果...   │                 │
│   │ 【少数派】 5. 用AI搭建个人知识库...   │                 │
│   └──────────────────────────────────────┘                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 快速开始

### 30 秒上手

```bash
# 1. 一键安装（全局可用）
npx skills add yqdaddy/dailyhot-skill --skill dailyhot-skill -a claude-code -g

# 2. 安装依赖 + 启动服务
cd ~/.claude/skills/dailyhot-skill
npm install && node scripts/start-server.mjs

# 3. 在 Claude Code 中说一句话
# "看看微博热搜"
```

---

## 架构概览

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   Claude Code    │     │   dailyhot-skill │     │   DailyHot API   │
│                  │     │                  │     │                  │
│  /dailyhot-skill │────▶│  SKILL.md        │────▶│  localhost:6688  │
│  "看看微博热搜"   │     │  query-hot.mjs   │     │                  │
│                  │     │  start-server.mjs│     │  56+ 数据源       │
└──────────────────┘     └──────────────────┘     └──────────────────┘
        触发                         调度                         抓取
```

**数据流向：**

```
你的请求 → Claude 识别意图 → 触发 dailyhot-skill
    → 启动本地查询脚本 → 调用 localhost:6688 API
    → API 从各平台公开接口拉取热榜 → 返回格式化数据
    → 脚本美化输出 → Claude 汇总呈现
```

---

## 安装方式

### 方式一：npx skills add（推荐）

**全局安装** — 所有 Claude Code 会话自动加载：

```bash
npx skills add yqdaddy/dailyhot-skill --skill dailyhot-skill -a claude-code -g
```

**项目级安装** — 仅当前项目：

```bash
npx skills add yqdaddy/dailyhot-skill --skill dailyhot-skill -a claude-code
```

<details>
<summary>安装效果示意</summary>

```
│  ✓ Installed 1 skill
│  ✓ dailyhot-skill (copied)
│    → ~/.claude/skills/dailyhot-skill
```

</details>

### 方式二：手动 clone

```bash
# 全局安装（推荐）
git clone https://github.com/yqdaddy/dailyhot-skill.git ~/.claude/skills/dailyhot-skill
cd ~/.claude/skills/dailyhot-skill && npm install

# 项目级安装
git clone https://github.com/yqdaddy/dailyhot-skill.git .claude/skills/dailyhot-skill
cd .claude/skills/dailyhot-skill && npm install
```

---

## 使用方式

### 自然语言触发

| 你说 | Claude 行为 |
|------|------------|
| "看看微博热搜" | 查询微博 Top 10 |
| "看看AI相关的热点" | 并行查 36kr + ithome + zhihu + sspai + bilibili，筛选AI相关 |
| "帮我汇总今日热点" | 并行查 5 大平台，输出综合热榜 |
| "今天大家都在关注什么" | 推荐平台供选择 |
| "抖音最近有什么热点" | 查询抖音热搜 |

### 斜杠命令触发

```
/dailyhot-skill           # 交互模式
/dailyhot-skill zhihu     # 查询知乎热榜
/dailyhot-skill weibo     # 查询微博热搜
/dailyhot-skill bilibili --limit 20  # 查询B站20条
```

---

## 功能详解

### 单平台查询

```
你: "看看知乎热榜"

📋 知乎热榜 · 知乎
🔗 https://www.zhihu.com/hot
📊 共 50 条 | 更新: 2026/05/26 14:30
────────────────────────────────────────────────────────────
 1. GPT-5 有哪些值得关注的改进
 2. 2026年AI编程工具实测效果如何
    AI编程工具在实际开发中能提升多少效率？多个团队实测数据显示...
    🔥 234.5 万
 3. ...
```

### 跨平台汇总查询

```
你: "看AI相关的热点，并帮我汇总到一起"

Claude 并行查询以下平台：
  36kr    ┐
  ithome  ├─ 科技相关平台 ──┐
  zhihu   │                 │
  sspai   │                 ├── 按"AI"关键词筛选
  bilibili┘                 │
                            └── 合并为一份报告

📊 AI热点汇总（2026/05/26 14:30）
────────────────────────────────────────────────────────────

【36氪】科技商业
  1. GPT-5 发布，多模态能力大幅提升        🔥 120 万
  2. 国内大模型加速追赶，差距缩小至半年

【IT之家】科技新闻
  1. 英伟达发布新一代GPU，AI推理性能翻倍    🔥 89 万
  2. 苹果自研AI芯片曝光，M5可能首发

【知乎】社区讨论
  1. 如何看待GPT-5的多模态能力             🔥 234.5 万
  2. AI编程工具实测，效率提升明显

【B站】视频内容
  1. 用AI搭建个人知识库，零基础教程         🔥 67.3 万
  2. AI绘画新工具，效果媲美Midjourney

【少数派】数字生活
  1. 10个值得尝试的AI效率工具              🔥 45.2 万
  2. 用AI自动化处理日常办公流程
```

---

## 平台列表

### 综合新闻（6 个）

| 平台 | 命令 | 热度图标 | 说明 |
|------|------|:--------:|------|
| 知乎 | `zhihu` | 📖 | 中文问答社区热榜 |
| 微博 | `weibo` | 🔥 | 全网实时热搜 |
| 百度 | `baidu` | 🔍 | 搜索引擎热搜 |
| 抖音 | `douyin` | 🎵 | 短视频平台热搜 |
| 快手 | `kuaishou` | 📹 | 短视频热榜 |
| 今日头条 | `toutiao` | 📰 | 资讯推荐热榜 |

### 科技/互联网（8 个）

| 平台 | 命令 | 说明 |
|------|------|------|
| B站 | `bilibili` | 热门视频/综合热门 |
| 36氪 | `36kr` | 科技商业资讯 |
| 少数派 | `sspai` | 数字生活/效率工具 |
| IT之家 | `ithome` | 科技新闻/数码产品 |
| CSDN | `csdn` | 开发者社区热榜 |
| 掘金 | `juejin` | 前端/后端/移动端技术 |
| V2EX | `v2ex` | 程序员社区 |
| GitHub | `github` | GitHub Trending |

### 媒体/社区（8 个）

| 平台 | 命令 | 说明 |
|------|------|------|
| 虎嗅 | `huxiu` | 商业评论 |
| 澎湃新闻 | `thepaper` | 时政新闻 |
| 果壳 | `guokr` | 科普热点 |
| 爱范儿 | `ifanr` | 科技媒体 |
| 豆瓣 | `douban` | 豆瓣热议 |
| 虎扑 | `hupu` | 体育/游戏社区 |
| 贴吧 | `tieba` | 百度贴吧热帖 |
| NGA | `ngabbs` | 游戏论坛 |

### 其他

地震速报、气象预警、历史上的今天、微信读书等。

运行 `node scripts/query-hot.mjs --all` 查看完整 56 个平台列表。

---

## 目录结构

```
dailyhot-skill/
│
├── SKILL.md                        # Claude Code 技能定义（根目录）
├── scripts/
│   ├── start-server.mjs            # 启动本地 API 服务
│   └── query-hot.mjs               # 查询热榜 + 格式化输出
├── package.json                    # 项目依赖
├── .gitignore                      # 忽略文件
└── README.md                       # 本文档
```

---

## 首次启动

```bash
# Step 1: 安装依赖
npm install

# Step 2: 启动 API 服务（端口 6688）
node scripts/start-server.mjs

# 输出: 🚀 Starting DailyHot API on port 6688...

# Step 3: 测试查询
node scripts/query-hot.mjs zhihu
```

> **注意**：服务启动后常驻后台运行，后续查询无需重启。端口 6688 已被占用时会自动跳过。

---

## 常见问题

<details>
<summary>❌ "无法连接到 DailyHot 服务"</summary>

服务未启动或已崩溃。重新运行：

```bash
node scripts/start-server.mjs
```

</details>

<details>
<summary>❌ 平台不存在</summary>

检查平台名称拼写，或运行 `node scripts/query-hot.mjs --all` 查看所有可用平台。

</details>

<details>
<summary>🔄 数据多久更新一次？</summary>

API 层默认 60 分钟缓存。各平台热榜本身实时更新，本地服务会在请求时尝试拉取最新数据。

</details>

<details>
<summary>⚙️ 如何修改 API 端口？</summary>

```bash
# 启动时指定端口
node scripts/start-server.mjs 3000

# 查询时指定 API 地址
DAILYHOT_URL=http://localhost:3000 node scripts/query-hot.mjs zhihu
```

</details>

---

## 技术栈

| 组件 | 说明 |
|------|------|
| [DailyHot API](https://github.com/imsyy/DailyHotApi) | 底层热榜聚合服务，MIT 协议 |
| Hono | 轻量级 Web 框架 |
| Node.js 20+ | 运行时 |
| Claude Code Skills | 技能封装层 |

---

## 更新技能

```bash
# 更新到最新版本
npx skills update dailyhot-skill -a claude-code -g
```

---

## License

本项目代码 [MIT](LICENSE)。底层 DailyHot API 同样 MIT 协议。
