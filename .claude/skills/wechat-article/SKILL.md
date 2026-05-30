---
name: wechat-article
description: 公众号全流程文章生成——热点抓取、选题、框架选择、写作、配图、排版、敏感词检查、发布。
when_to_use: 当用户提到"写公众号"、"写推文"、"公众号文章"、"微信推文"、"写一篇"时使用此技能。
---

# 公众号文章全流程工作流

## 首次使用安装

如果是第一次使用，需要先安装依赖：

```bash
# 安装 Python CLI 和 MCP Server
pip install git+https://github.com/yqdaddy/mamacore.git

# 注册 MCP Server 到 Claude Code
claude mcp add mamacore -- mama-server

# 安装热榜服务依赖（仅需一次）
cd "$(python -c 'import mamacore; from pathlib import Path; print(Path(mamacore.__file__).parent.parent.parent / "services/dailyhot")')" && npm install
```

安装完成后重新触发本技能即可。

## 前置检查

确认以下 MCP 工具可用：
- `mama_hot_topics` (热点)
- `mama_write_article` (写作)
- `mama_score_title` (标题评分)
- `mama_format_article` (排版)
- `mama_generate_images` (配图)
- `mama_check_sensitive` (敏感词)
- `mama_publish_draft` (发布)

如果工具不可用，请先运行安装命令。

## 步骤 1: 热点分析

调用 `mama_hot_topics(source="gzh", count=20)` 获取公众号爆款热点。
根据用户输入的主题，筛选相关热点话题。
如果用户已提供明确主题，可跳过此步直接进入选题。

## 步骤 2: 选题确认

结合热点和用户输入确定选题。
输出选题声明："今天我们来聊聊 [选题]，因为 [热点背景]"。

## 步骤 3: 框架选择

根据选题类型选择文章框架:
- **checklist** (清单型): 适用于攻略、指南、盘点、避坑
- **pain** (痛点型): 适用于焦虑、困惑、误区、解决方案
- **compare** (对比型): 适用于选型、评测、A vs B
- **narrative** (叙事型): 适用于经历分享、案例故事、个人感悟

调用 `mama_write_article(topic=选题, framework=框架, style=风格)` 生成文章。

## 步骤 4: 标题优化

调用 `mama_score_title` 对推荐标题进行评分。
展示前 3 个标题选项及评分，让用户选择。
如果没有满意的标题，调用 `mama_write_article` 重新生成。

## 步骤 5: 配图生成

如果用户要求或 `include_images=true`:
调用 `mama_generate_images(topic=选题, image_count=3)` 生成封面和内文配图。

## 步骤 6: 排版转换

调用 `mama_format_article(article_md=文章, theme="default")` 将 Markdown 转为公众号 HTML。
展示排版后的效果（前 2000 字符）。

## 步骤 7: 敏感词检查

调用 `mama_check_sensitive(text=文章全文)` 进行安全检测。
- 如果有高风险词：标注位置，建议替换
- 如果通过：继续下一步

## 步骤 8: 发布草稿

调用 `mama_publish_draft(title=标题, content=HTML内容)` 发布到公众号草稿箱。
告知用户草稿已创建，如为个人号需手动点击发布。

## 可选步骤: 多平台同步

如果用户要求同步到其他平台:
调用 `mama_sync_to_platforms(article_path=文章文件, platforms="zhihu,toutiao,csdn")`。

## 注意事项

- 每个步骤完成后询问用户是否需要修改或继续
- 如果用户在某步骤提出修改意见，返回对应步骤重新执行
- 保持风格一致性：如果用户有历史风格配置，优先使用

## 环境变量要求

- `OPENAI_API_KEY` 或 `ANTHROPIC_API_KEY` (LLM 调用)
- `MAMA_WECHAT_APP_ID` / `MAMA_WECHAT_APP_SECRET` (公众号 API)
