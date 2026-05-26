/**
 * M.A.M.A. Core 热榜聚合服务
 * 基于 DailyHotApi，启动本地 HTTP 服务供 Python 端调用
 *
 * 启动: pnpm start
 * 访问: http://localhost:6688/weibo
 */

import serveHotApi from "dailyhot-api";

const PORT = parseInt(process.env.DAILYHOT_PORT || "6688", 10);

console.log(`[dailyhot] 正在启动热榜服务，端口 ${PORT}...`);

try {
  await serveHotApi(PORT);
  console.log(`[dailyhot] 服务已启动: http://localhost:${PORT}`);
  console.log(`[dailyhot] 可用接口: http://localhost:${PORT}/weibo, /zhihu, /toutiao 等`);
} catch (error) {
  console.error("[dailyhot] 启动失败:", error.message);
  process.exit(1);
}
