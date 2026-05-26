"""发布与多平台同步模块 -- 公众号 + 知乎/头条/CSDN 分发。"""

from .wechat_api import create_draft, publish, get_account_type, upload_material
from .multisync import sync_to_platforms
from .scheduler import schedule_publish, list_scheduled_tasks, cancel_publish


def register_tools(mcp) -> None:
    """向 MCP Server 注册本模块的所有 tools。"""

    @mcp.tool()
    async def mama_publish_draft(
        title: str,
        content: str,
        cover_media_id: str = "",
        author: str = "",
        auto_publish: bool = True,
    ) -> str:
        """发布文章到公众号草稿箱。服务号可直接发布。

        Args:
            title: 文章标题
            content: 文章 HTML 内容（已通过 mama_format_article 转换）
            cover_media_id: 封面图 media_id（可选）
            author: 作者名（可选）
            auto_publish: 是否自动发布（仅服务号有效）
        """
        try:
            media_id = await create_draft(title, content, cover_media_id, author)
            account_type = await get_account_type()

            lines = ["## 发布结果"]
            lines.append(f"- 草稿 ID: {media_id}")
            lines.append(f"- 账号类型: {account_type}")

            if auto_publish and account_type == "service":
                pub_result = await publish(media_id)
                lines.append(f"- 发布状态: 已发布")
                lines.append(f"- 发布 ID: {pub_result.get('publish_id', 'N/A')}")
            else:
                lines.append(f"- 发布状态: 草稿已创建")
                if account_type == "personal":
                    lines.append(
                        f"- 个人号需要手动在公众号后台点击发布"
                    )

            return "\n".join(lines)
        except Exception as e:
            error_msg = str(e)
            if "MAMA_WECHAT_APP_ID" in error_msg or "MAMA_WECHAT_APP_SECRET" in error_msg:
                hint = "请先在公众号后台获取 AppID 和 AppSecret，然后设置环境变量：\n  export MAMA_WECHAT_APP_ID=xxx\n  export MAMA_WECHAT_APP_SECRET=xxx"
            elif "微信 API 错误" in error_msg:
                hint = "请检查公众号账号状态和 API 权限。"
            else:
                hint = f"详细错误: {e}"
            return f"发布失败\n\n{hint}"

    @mcp.tool()
    async def mama_sync_to_platforms(
        article_path: str,
        platforms: str,
    ) -> str:
        """同步文章到多个平台（知乎/头条/百家号/CSDN等）。

        Args:
            article_path: 文章文件路径（Markdown 或 HTML）
            platforms: 目标平台列表，用逗号分隔
                (zhihu/toutiao/baijiahao/csdn/juejin)
        """
        platform_list = [
            p.strip() for p in platforms.split(",") if p.strip()
        ]
        results = await sync_to_platforms(article_path, platform_list)

        lines = ["## 多平台同步结果\n"]
        for platform, result in results.items():
            if result["status"] == "success":
                status = "成功"
            else:
                status = f"失败: {result.get('error', '未知错误')}"
            lines.append(f"- {platform}: {status}")
        return "\n".join(lines)

    @mcp.tool()
    async def mama_schedule_publish(
        title: str,
        content: str,
        task_id: str = "",
        publish_time: str = "",
    ) -> str:
        """预约发布。在指定时间自动将文章发布到公众号。

        Args:
            title: 文章标题
            content: 文章 HTML 内容
            task_id: 任务 ID（自动生成随机 ID 如果为空）
            publish_time: 发布时间，格式 YYYY-MM-DD HH:MM
                （默认 1 小时后）
        """
        import uuid
        from datetime import datetime

        tid = task_id or str(uuid.uuid4())[:8]

        pub_time = None
        if publish_time:
            try:
                pub_time = datetime.strptime(publish_time, "%Y-%m-%d %H:%M")
            except ValueError:
                return (
                    "时间格式错误。请使用 YYYY-MM-DD HH:MM 格式，"
                    f"例如: 2026-05-24 21:30"
                )

        tid = schedule_publish(tid, title, content, pub_time)
        task = list_scheduled_tasks()[-1]
        return (
            f"## 预约发布成功\n\n"
            f"- 任务 ID: {tid}\n"
            f"- 标题: {title}\n"
            f"- 发布时间: {task['publish_time']}\n"
            f"- 延迟: {task['delay_seconds']:.0f} 秒后"
        )
