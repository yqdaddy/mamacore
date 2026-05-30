# 贡献指南

感谢你考虑为 M.A.M.A. Core 做出贡献！

## 开发环境设置

```bash
# 克隆项目
git clone https://github.com/yqdaddy/mamacore.git
cd mamacore

# 安装依赖
uv sync --all-extras

# 运行测试
uv run pytest
```

## 代码规范

- 使用 `ruff` 进行代码检查：`uv run ruff check src/`
- 中文注释，中英文之间加空格
- 新增 MCP tool 必须在对应模块的 `register_tools()` 中注册，并写好 docstring
- MCP 走 stdio 通信，**禁止 print 到 stdout**（用 stderr）

## 提交 Pull Request

1. Fork 本仓库
2. 创建特性分支：`git checkout -b feat/your-feature`
3. 提交更改：`git commit -m 'feat(模块): 描述'`
4. 推送分支：`git push origin feat/your-feature`
5. 提交 Pull Request

### 提交消息规范

遵循 Conventional Commits 格式：

```
feat(热点): 接入微博热搜 API
fix(排版): 修复容器语法渲染 bug
docs(README): 补充 FAQ 章节
```

类型可选：`feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`

## 添加新模块

1. 在 `src/mamacore/` 下创建新目录
2. 创建 `__init__.py` 并定义 `register_tools(mcp)` 函数
3. 在 `server.py` 的 `_register_tools()` 模块列表中添加新模块
4. 更新 `README.md` 的 MCP Tools 索引表

## 报告 Bug

请使用 GitHub Issues 报告问题，并包含以下信息：

- Python 版本和操作系统
- 复现步骤
- 预期行为和实际行为
- 错误日志（如有）
