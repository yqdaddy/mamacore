#!/bin/bash
# 一键安装并启动 DailyHotApi 服务
# 需要 Node.js >= 18 和 pnpm

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== M.A.M.A. Core 热榜服务启动 ==="

# 检查 Node.js
if ! command -v node &> /dev/null; then
  echo "❌ 未找到 Node.js，请先安装 (https://nodejs.org/)"
  exit 1
fi
echo "✅ Node.js: $(node --version)"

# 检查 pnpm
if ! command -v pnpm &> /dev/null; then
  echo "⚠️  pnpm 未安装，正在安装..."
  npm install -g pnpm
fi
echo "✅ pnpm: $(pnpm --version)"

# 安装依赖
echo "📦 安装依赖..."
pnpm install --production

# 启动服务
PORT="${DAILYHOT_PORT:-6688}"
echo "🚀 启动热榜服务 (端口 ${PORT})..."
pnpm start
