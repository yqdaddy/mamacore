"""数据分析模块 —— 采集/指标/选题/爆款模式/策略推荐。"""

from .models import ArticleMetrics, AccountProfile
from .scraper import fetch_account_articles, load_articles, import_csv, save_articles
from .metrics import calculate_account_profile, get_top_articles, get_trend


def register_tools(mcp) -> None:
    """向 MCP Server 注册本模块的所有 tools。"""

    @mcp.tool()
    async def mama_analyze_account(
        account_id: str,
        days: int = 30,
    ) -> str:
        """分析指定公众号的历史文章数据，计算账号画像和核心指标。

        Args:
            account_id: 公众号 ID 或名称
            days: 分析时间范围（天）
        """
        try:
            await fetch_account_articles(account_id, days)
        except Exception as e:
            # 如果 API 不可用，尝试从本地数据库加载
            articles = load_articles(account_id, days)
            if not articles:
                return (
                    f"数据采集失败：{e}\n\n"
                    "请确保 wechat-article-exporter 服务正在运行"
                    "（设置 MAMA_EXPORTER_URL 环境变量），"
                    "或先用 mama_import_metrics 导入历史数据。"
                )

        profile = calculate_account_profile(account_id, days)
        top_articles = get_top_articles(account_id, days, limit=5)
        trend = get_trend(account_id, days)

        lines = [
            f"## 账号画像 ({account_id}, 最近 {days} 天)",
            f"- 文章总数: {profile.total_articles}",
            f"- 平均阅读: {profile.avg_reads}",
            f"- 平均点赞: {profile.avg_likes}",
            f"- 平均互动率: {profile.avg_interaction_rate:.2%}",
            f"- 最佳发文时间: {profile.best_publish_hour}:00",
            "",
            "### 阅读排行 Top 5",
        ]
        for i, a in enumerate(top_articles, 1):
            lines.append(
                f"{i}. {a['title']} — 阅读 {a['reads']}, 互动率 {a['interaction_rate']:.2%}"
            )

        return "\n".join(lines)

    @mcp.tool()
    async def mama_import_metrics(csv_path: str, account_id: str) -> str:
        """从 CSV 文件手动导入历史文章数据。

        CSV 格式: article_id,title,url,published_at,read_count,like_count,comment_count,share_count,is_original

        Args:
            csv_path: CSV 文件路径
            account_id: 公众号 ID
        """
        count = import_csv(csv_path, account_id)
        return f"已导入 {count} 篇文章数据到 {account_id}。"

    @mcp.tool()
    async def mama_topic_heatmap(
        account_id: str,
        days: int = 30,
    ) -> str:
        """生成选题热力图：哪些话题在你的账号上表现最好。

        Args:
            account_id: 公众号 ID
            days: 分析天数
        """
        from .topic_analysis import get_topic_heatmap
        result = get_topic_heatmap(account_id, days)

        lines = [f"## 选题热力图 ({account_id}, {days}天)\n"]
        if result["hot_topics"]:
            lines.append("### 热门话题（表现优于平均）")
            for t in result["hot_topics"]:
                lines.append(
                    f"- {t['topic']}: 平均阅读 {t['avg_reads']}, "
                    f"互动率 {t['avg_interaction_rate']:.2%}, "
                    f"{t['article_count']}篇"
                )
        if result["cold_topics"]:
            lines.append("\n### 冷门话题（表现低于平均）")
            for t in result["cold_topics"]:
                lines.append(
                    f"- {t['topic']}: 平均阅读 {t['avg_reads']}, "
                    f"{t['article_count']}篇"
                )
        return "\n".join(lines)

    @mcp.tool()
    async def mama_content_strategy(
        account_id: str,
        days_ahead: int = 7,
    ) -> str:
        """生成下周内容策略报告（核心亮点工具）。

        综合选题热力图、标题模式、爆款模式、发文排期，输出"接下来该写什么"的策略建议。

        Args:
            account_id: 公众号 ID
            days_ahead: 策略覆盖天数（默认 7 天）
        """
        from .recommender import generate_content_strategy
        result = generate_content_strategy(account_id, days_ahead)

        lines = [f"## 内容策略报告 ({account_id}, 未来 {days_ahead}天)\n"]
        lines.append("### 核心建议")
        lines.append(f"{result['summary']}\n")

        if result["hot_topics"]:
            lines.append("### 优先话题")
            for t in result["hot_topics"]:
                lines.append(f"- {t}")

        if result["untapped_topics"]:
            lines.append("\n### 机会话题（你还没写过的）")
            for t in result["untapped_topics"]:
                lines.append(f"- {t}")

        lines.append("\n### 标题模式建议")
        lines.append(f"- 最佳模式: {result['best_title_pattern']}")

        lines.append("\n### 发文排期")
        for s in result["publish_schedule"]:
            rec = "推荐" if s.get("recommended") else "可选"
            lines.append(
                f"- {s['date']} ({s['day']}) {s['hour']}:00 [{rec}]"
            )

        return "\n".join(lines)

    @mcp.tool()
    async def mama_competitor_gap(
        my_account: str,
        competitors: str,
        days: int = 30,
    ) -> str:
        """对比竞品账号，找到内容差距和机会点。

        Args:
            my_account: 我的公众号 ID
            competitors: 竞品账号列表，逗号分隔
            days: 分析天数
        """
        from .competitor import compare_competitors
        comp_list = [c.strip() for c in competitors.split(",") if c.strip()]
        result = compare_competitors(my_account, comp_list, days)

        lines = ["## 竞品对标分析\n"]
        lines.append(f"- 我的账号: {result['my_account']}")
        lines.append(f"- 话题覆盖: {result['my_topic_count']} 个")
        lines.append("\n### 内容差距")
        if result["gaps"]:
            for g in result["gaps"]:
                lines.append(f"- {g}")
        else:
            lines.append("未发现明显差距。")

        if result["opportunities"]:
            lines.append("\n### 机会点")
            for o in result["opportunities"]:
                lines.append(f"- {o}")
        return "\n".join(lines)
