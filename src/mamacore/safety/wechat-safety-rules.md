---
name: wechat-safety-rules
description: 微信公众号风控规则与安全检查流程（2026-04 更新）
type: reference
---

**位置**：`safety/wechat-risk-rules.md` — 风控规则文档
**检查工具**：`safety/safety_checker.py` — 发布前自动审查脚本

**使用方式**：
```bash
.venv/bin/python safety/safety_checker.py output/文章路径.md
```

**风险等级**：
- 🔴 HIGH：高危内容，建议立即修改
- 🟡 MEDIUM：中等风险，需要检查
- 🟢 LOW：低风险，内容基本合规
- ✅ SAFE：安全，无风险

**Why**：2026 年微信封号力度加大，临时封号从 7 天延长至 15 天起步，严重违规直接永久封号。需要事前检查规避风险。

**How to apply**：每次发布文章前运行 `safety_checker.py`，根据检查结果修改内容。重点关注：引流话术、诱导分享、敏感词。