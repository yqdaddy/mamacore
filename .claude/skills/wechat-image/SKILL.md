---
name: wechat-image
description: 公众号配图生成——封面图、内文配图、分享卡片。
when_to_use: 当用户提到"生成封面"、"生成配图"、"做张封面"、"配图"时使用此技能。
---

# 图片生成工作流

## 首次使用安装

如果是第一次使用，需要先安装依赖：

```bash
pip install git+https://github.com/yqdaddy/mamacore.git
claude mcp add mamacore -- mama-server
```

安装完成后重新触发本技能即可。

## 前置检查

确认以下 MCP 工具可用：
- `mama_generate_images` (批量生成配图)
- `mama_generate_cover` (生成封面图)
- `mama_list_image_templates` (列出模板)

## 步骤 1: 查看可用模板

调用 `mama_list_image_templates` 查看可用图片提示词模板。
根据文章类型推荐模板（技术类→tech_cover，生活类→lifestyle_inline）。

## 步骤 2: 生成图片

调用 `mama_generate_images(topic=主题, image_count=3, style=风格)` 批量生成。
或调用 `mama_generate_cover(topic=主题, style=风格)` 单独生成封面。

## 步骤 3: 展示结果

展示生成的图片 URL、提示词、尺寸信息。
询问用户是否满意，不满意可调整风格或提示词后重新生成。

## 注意事项

- 需要设置对应的 API Key（OPENAI_API_KEY 或 DASHSCOPE_API_KEY）
- 不同风格适用于不同类型文章
