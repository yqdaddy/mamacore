---
name: wechat-article
description: 数据驱动的公众号爆款工作流 —— 先分析热榜和竞品数据，再生成文章。与 wewrite 的区别：本技能侧重"数据分析→爆款选题→多平台分发"，wewrite 侧重"单篇内容创作→排版→发布"。
when_to_use: 当用户说"公众号爆款"、"爆款文章"、"数据驱动"、"竞品分析"、"对标账号"、"选题热力图"、"下周写什么"、"看看最近什么火"时使用。如果用户只说"写一篇公众号文章"或"写推文"，优先使用 wewrite。
---

# 数据驱动的公众号爆款工作流

## 前置检查

确认以下 MCP 工具可用：
- `mama_hot_topics` (热点)
- `mama_write_article` (写作)
- `mama_score_title` (标题评分)
- `mama_format_article` (排版)
- `mama_generate_images` (配图)
- `mama_check_sensitive` (敏感词)
- `mama_publish_draft` (发布)

## 步骤 1: 热点分析

调用 `mama_hot_topics(source="gzh", count=20)` 获取公众号爆款热点。

## 步骤 2: 选题确认

结合热点和用户输入确定选题。

## 步骤 3: 框架选择

调用 `mama_write_article(topic=选题, framework=框架, style=风格)` 生成文章。

## 步骤 4: 标题优化

调用 `mama_score_title` 对推荐标题进行评分。

## 步骤 5: 配图生成

调用 `mama_generate_images(topic=选题, image_count=3)` 生成配图。

## 步骤 6: 排版转换

调用 `mama_format_article(article_md=文章, theme="default")` 转为公众号 HTML。

## 步骤 7: 敏感词检查

调用 `mama_check_sensitive(text=文章全文)` 进行安全检测。

## 步骤 8: 发布草稿

调用 `mama_publish_draft(title=标题, content=HTML内容)` 发布到草稿箱。
