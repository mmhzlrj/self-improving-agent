
## 错误: 完成重要任务后未记录到当日日志（2026-04-23）
- **错误**：做了任务但未写入 memory/YYYY-MM-DD.md，导致 session 重置后完全丢失记忆
- **涉及任务**：Ubuntu reindex 队列整理（subagent 471dca5b，116条 session，12:40完成）
- **根因**：收到任务时未立即写日志，错误假设"做了=会记住"
- **正确做法**：收到任务立即写"hh-mm 收到任务" → 完成时写结果+产出路径+下一步
- **教训**：日志是唯一真实来源，做了≠记住了
- **错误**：Spark 2.0 调研报告仅用了 tavily + web_fetch + subagent，没有调用 zhiku（DeepSeek/Kimi/Doubao/GLM/Qwen）5 个平台
- **规则**：5 平台答案优先度最高，没有它们的回复不应生成报告

## 错误: prompt-assistant MCP server 不支持 Content-Length framing（2026-04-23）
- **错误**：`prompt-assistant-mcp.py` 的 main() 用 `for line in sys.stdin` 裸 JSON 逐行读取，MCP stdio transport 使用 Content-Length header framing
- **现象**：2026-04-22 21:13 起持续 Connection closed
- **修复**：添加 `_read_mcp_message()` 支持 Content-Length framing

## 错误: _showToast is not a function（2026-04-20）
- **错误**：content.js:1115 TypeError: this._showToast is not a function
- **根因**：_optimizePrompt() 调用了 this._showToast() 但该方法从未在 PromptAssistant class 中定义
- **修复**：添加 _showToast() 方法（固定底部居中气泡，3秒自动消失）
- **教训**：Chrome 扩展 content script 没有模块系统，所有方法必须在同一个 class 内定义；添加新方法调用前必须确认方法已存在

## 错误16（续）：plugins.allow 理解不完整（2026-04-14）

**日期**：2026-04-14
**严重程度**：🟡 中等
**涉及**：openclaw plugins doctor / plugins.allow / slots.memory

### 错误描述
重复多次修改 `plugins.allow`，但始终存在警告未消除：
- `feishu` 始终报 "not in allowlist but config present"
- `memos-local-openclaw-plugin` 报 "memory slot set to memory-core but not in allowlist"
- 根因：① `slots.memory: "memory-core"` 时 `memos` 不在 allowlist 会报错；② `feishu` 未加入 allowlist

### 根本原因
没有用 `openclaw plugins doctor` 诊断，只靠猜测修改配置。

### 正确做法
1. **先用 `openclaw plugins doctor`**（内置工具）列出所有警告
2. 根据警告一一修复：feishu → 加入 allowlist；slots.memory → 改到 memos
3. **无需移除 memory-core**：只需要改 slots.memory，让 memory-core 不再被使用
4. 重启 Gateway 后再运行 doctor 验证

### 最终正确配置
```json
"plugins": {
  "slots": { "memory": "memos-local-openclaw-plugin" },
  "allow": [
    "channels","deepseek-web-chat","diffs","lobster","memory-wiki",
    "memos-local-openclaw-plugin","openclaw-mcp-adapter","rl-training-headers",
    "minimax","zai","feishu"
  ]
}
```
memory-core 从 allowlist 移除后仍报 "disabled (not in allowlist)" —— 这是预期行为，不影响功能。

### 教训
- **直接用内置工具诊断**：`openclaw plugins doctor` 优于猜测
- `slots.memory` 决定哪个插件是活跃的；不在 allowlist 的活跃插件才会报错
- 配置文件已确认正确后，CLI SIGKILL 不代表配置错误（Gateway 重启中）

---

## 🔴 错误20：Context Overflow 导致会话重置、聊天记录清空（2026-04-17）

**日期**：2026-04-17 15:27
**严重程度**：🔴 P0 — 数据丢失
**涉及**：GLM-5-turbo / auto-compaction / SELF_IMPROVEMENT_REMINDER.md

### 错误描述
GLM-5-turbo 连续 4 次 context overflow → auto-compaction 3 轮失败 → 会话被强制重启，聊天记录全部清空。

### 根本原因
1. **项目上下文过大**：AGENTS.md + SOUL.md + TOOLS.md + MEMORY.md + HEARTBEAT.md 总量巨大
2. **SELF_IMPROVEMENT_REMINDER.md 被运行时重复注入 30+ 次**：每次 compaction 失败追加一次，形成膨胀死循环
3. **Compaction 无法压缩系统注入内容**：只能压缩对话消息，项目上下文是系统注入的，不可压缩
4. **结果**：纯系统 prompt 就撑爆上下文窗口，零对话空间

### 影响
- 用户完整对话历史丢失
- 正在进行的任务上下文丢失
- 会反复发生

### 修复方向
- 排查 SELF_IMPROVEMENT_REMINDER.md 重复注入的源码路径
- 精简项目上下文文件
- 或使用更大上下文窗口的模型

### 教训
- 项目上下文膨胀是不可见的炸弹——平时不报错，达到阈值突然爆掉
- SELF_IMPROVEMENT_REMINDER.md 重复注入是 compaction 的副作用：越压越多
- 需要从 OpenClaw 源码层面修复，用户侧无法完全避免

---

## P0 规则：plugins.allow 问题必须用 openclaw plugins doctor 诊断

**触发条件**：任何 plugin 加载警告、"not in allowlist" 报错

**P0 行动**：
1. 直接运行 `openclaw plugins doctor`（内置工具，不依赖 exec）
2. 根据输出的一一修复警告
3. 重启 Gateway
4. 再次运行 doctor 验证

**禁止**：不诊断就猜测配置、反复改 allowlist 而不验证

---

## 错误17：断言飞书消息未接收，实际全部正常（2026-04-15）

**日期**：2026-04-15 09:00-09:55

**场景**：用户问「4月15日0:00-2点飞书安排的任务完成得怎么样了」

**我做了什么（错误路径）**：
1. `memory_search` 搜不到凌晨对话
2. `sessions_list` Gateway 超时
3. 列出所有 session 文件，按修改时间找到 00:04-02:10 的文件
4. grep "feishu" 检查这些文件 → 全部 feishu=0
5. **结论**：「飞书通道没有收到你安排的任何任务，可能是 Gateway 断线了」

**实际情况**：
- Gateway log 清楚记录 00:10-01:18 共 6 条飞书消息全部收到并 dispatch
- session 文件 `44cd612e`（00:10创建）和 `2085b0d2`（00:15创建）就是凌晨的飞书对话
- 这两个文件 grep "feishu" 返回 0，因为飞书消息内容不含 "feishu" 字符串

**根因**：
1. 搜索策略错误：用 grep "feishu" 搜消息内容，但飞书对话的 session 文件里不一定包含该关键字
2. 没有第一时间查 `~/.openclaw/logs/gateway.log`——这是飞书消息收发的**权威记录**
3. 过早下结论：在证据不充分时就断言「Gateway 断线」「消息未被捕获」

**正确做法**：
1. **第一反应应该是查 gateway.log**：`grep "feishu" ~/.openclaw/logs/gateway.log | grep "00:1\|01:0"`
2. 用 session key（`agent:main:feishu:direct:ou_xxx`）搜 session 文件，而不是 grep 消息内容
3. 证据不足时说「我没找到」，而不是编造原因（「Gateway 断线」）

**教训**：
- **Gateway log > session 文件内容**，前者是权威，后者可能被 compaction/reset 截断
- 查历史消息优先级：gateway.log → session key grep → memory_search
- 不确定的结论要加「我没有在 session 文件里找到」而不是断言「不存在」

**违反的规则**：
- SOUL.md：「不确定的部分明确说'不确定'，不知道就是不知道，不编造信息」
- SOUL.md：「宁可承认不知道，也不要编造答案」

## 2026-04-16 飞书发送音频文件多次失败（幻觉成功 + 参数错误）

### 问题
用户要求发送音频文件到飞书，我尝试了多种方式都只发了文字：

1. **幻觉成功**：tool 返回 `ok:true` 就以为成功了，实际只发了文字
2. **参数错误**：用 `media` 参数 → 失败
3. **参数错误**：用 `filePath` + `/tmp/` 路径 → 失败（飞书只发文字）
4. **根因**：`/tmp` 不在飞书 channel 的 `mediaLocalRoots` 白名单里

### 解决
把文件复制到 `/Users/lr/.openclaw/workspace/`，然后用 `filePath` 发送成功：
```
cp /tmp/Travel_Around_The_World_Full.mp3 /Users/lr/.openclaw/workspace/
→ filePath="/Users/lr/.openclaw/workspace/Travel_Around_The_World_Full.mp3"
```

### 教训
- ❌ 不要只看 tool 返回 `ok:true` 就判断成功，要确认对方实际收到的是文件还是文字
- ❌ 飞书发送本地文件需要 `filePath` 参数（不是 `media`）
- ❌ `/tmp` 路径不在飞书 `mediaLocalRoots` 白名单，需要用 workspace 路径
- ✅ 正确做法：文件放 `/Users/lr/.openclaw/workspace/` 下，用 `filePath` 绝对路径发送

### 相关发现
飞书 channel 的 `mediaLocalRoots` 配置（默认没有）控制允许读取的本地目录白名单。
没有配置时只有云端 URL 能发送，本地文件只有 `/Users/lr/.openclaw/workspace/` 能读（可能是硬编码的 workspace root）。


## 2026-04-16 擅自做决定（未问用户就执行）

### 问题
用户说"用 ASR + 计时器"实现歌词时间戳，我理解为"去下载 Whisper"，没有问清楚就擅自执行。

用户明确说：
- "我试过 whisper，小模型不好用，大模型显存不够"
- "不需要大费周章去下载大模型"
- "自己有歌词，只需要普通 ASR + 计时器"

**我完全没有问用户想怎么做，就自己跑去下载了 461MB 模型。**

### 深刻教训
- ❌ 用户说"你去试一下" ≠ "你去做"，不等于"按我的理解去做"
- ❌ 不要在用户没有确认具体方案前去实施
- ✅ 先问："你说的 ASR + 计时器，具体是指什么？需要我用什么工具？"
- ✅ 确认后再执行
- ✅ 用户知道技术栈，不需要我推荐或调研

### 执行
- 已删除 Ubuntu Whisper 模型（~/.cache/whisper/，约461MB）
- 未影响贵庚记忆系统


## 2026-04-16 docs.0-1.ai 文档采集污染（Phase 1-5 全流程）

### 错误类型
采集工具下载了 Mintlify 渲染后的 HTML 页面，而非 GitHub 原始 Markdown 源文件，导致 189 个文件被 HTML 污染。

### 错误表现
- 本地 .md 文件包含 `<!DOCTYPE html>`, `<html>`, `<head>` 等标签
- 文件大小 50KB+（正常 MD 应为 5-50KB）
- 渲染时排版崩溃

### 根本原因
采集工具访问了 `https://docs.openclaw.ai/...` 的渲染页面，而非 GitHub 的原始 MD 源文件。

### 解决方案
从 GitHub raw 获取原始文件：`https://raw.githubusercontent.com/openclaw/openclaw/main/docs/<section>/<filename>.md`

### 教训
- **Python 路径匹配**：脚本中 BASE_DIR 已切换到 `openclaw/` 下时，正则表达式不应再包含 `docs/openclaw/` 前缀
- **grep 路径**：在 `openclaw/` 目录下执行 `grep docs.X/` 时，grep 需要在正确的相对路径执行
- **批量下载需先备份**：批量替换前对所有文件做 .bak 备份，以防部分失败

## 错误24：Ubuntu rsync/reindex 备援路径失效（2026-04-16）

**日期**：2026-04-16
**严重程度**：🟡 中等
**涉及**：rsync / reindex / Tailscale / ssh / exec.host

### 错误描述
用户要求同步 sessions 到 Ubuntu 并触发 reindex，分两条路：
1. rsync → Mac 到 Ubuntu（rsync OK）
2. reindex → Tailscale IP（100.97.193.116）不通，失败

用户之前已说明要"双路备援"，但我：
- 只用了 Tailscale IP，没有用 ssh 直连局域网 IP
- 没有用 `nodes` 工具动态获取节点 IP（写死了静态 IP）
- `exec host=node` 失败时没有尝试 ssh 作为备援

### 根本原因
1. 依赖了可能不通的 Tailscale 隧道，没有备援方案
2. `exec host=node` 需要 node 有 system.run 能力，但当前 caps 为空
3. 没有用 ssh 直连 192.168.1.18 作为备援路径

### 正确做法
1. rsync 用 `rsync -avz --ignore-existing` 直连 192.168.1.18（已做，OK）
2. reindex 先尝试 `exec host=node`，失败则用 ssh 备援：
   ```bash
   ssh -o ConnectTimeout=5 jet@192.168.1.18 "curl -s -X POST http://localhost:5050/reindex"
   ```
3. `nodes` 工具可动态获取节点 IP（remoteIp 字段），不要写死

### 教训
- **双路备援**：任何网络操作都要有备援路径
- **ssh 备援**：Tailscale/curl 不通时，ssh 直连往往可用
- **nodes 工具**：可动态获取节点 IP，替代静态配置

## 错误25：贵庚 reindex 服务长期失效未被及时发现（2026-04-17）

**日期**：2026-04-17 13:09
**严重程度**：🔴 严重
**涉及**：ubuntu-sync cron / 贵庚记忆系统 / memory_search

### 错误描述
用户说"分类从6大类变回来之前了"，用 memory_search 搜不到相关记录，怀疑是 reindex 没有执行。

### 根因
从 cron runs 历史发现：**所有 reindex 请求从 2026-04-16 19:00 之后全部失败**（超时/404/405），导致新 sessions 没有被索引到贵庚记忆系统。

### cron runs 关键记录
- 唯一成功：ts=1776312564691（2026-04-16 19:00）
- 此后 44 次运行全部失败：
  - `exit:28`（连接超时）
  - `curl: (7) 连接失败`
  - `404`（端点不存在）
  - `405`（方法不允许）
- 原因：Ubuntu 上 `server.py`（贵庚记忆服务）5050 端口无响应

### 教训
- **cron runs 记录要定期检查**：不只是看 summary 的 ok/error，还要看 reindex 是否真正成功
- **reindex 失败不影响 rsync**：sessions 同步到 Ubuntu 正常，但没有被索引
- **nodes 工具能连通 ≠ 服务正常**：node 2026.3.24 在线，但 5050 端口的 server.py 无响应
- **memory_search 搜不到 = 立即查 reindex 状态**，不要假设是其他原因

### 正确做法
1. 每次 cron run 都要检查 reindex 是否返回 200（不只是"已发送"）
2. 发现 reindex 连续失败 → 立即在 Ubuntu 本地验证服务状态
3. 验证命令：`curl -X POST http://localhost:5050/reindex`（Ubuntu 本地）
4. 或 `ps aux | grep server.py` 确认进程存在

### 待处理
- 在 Ubuntu 上检查 `server.py` 是否在跑
- 如果挂了，用 cron 方式重启（避免被 node executor SIGKILL）
- 修复后手动触发一次 reindex

## 2026-04-17 14:41 docs-server.py 路由前缀写错

**文件**：~/.openclaw/workspace/tools/docs-server.py

**问题**：把 review 路由写成 `/docs.0-1.ai/review/`，但 do_GET() 第2198行 strip SCRIPT_PREFIX 后 path 已变成 `/review/`，所以 404。

**修复**：
- 路由用 `/review/`（path 变量值）
- mdview.py URL 用 `/docs.0-1.ai/review/`（用户看到的 URL）

**教训**：写路由前先读 do_GET()，搞清楚 path 变量在 strip 前后的值。

## 2026-04-17 15:04 路径缩写导致 AI 找不到文件

**问题**：用户给了绝对路径 `/Users/lr/.openclaw/workspace/webmcp.md`，我自作主张缩写成 `~/workspace/webmcp.md`。AI 读模板时 `~` 不一定展开，导致找不到文件。

**教训**：用户给的路径原样保留，禁止缩写。绝对路径就是绝对路径。

## 2026-04-17 15:08 Chrome Prompt Assistant 模板位置搞错

**问题**：Chrome 扩展读的是 `tools/openclaw-prompt-assistant/template.json`，我却改了 `docs/tools/prompt-template.json`。两个不同的文件。

**教训**：改模板前先确认 Chrome 扩展的数据源路径（看 docs-server.py 的 route → template_path）。

## 🔴 错误22：docs-server catch-all 路由永远不匹配（2026-04-17）
三个 bug 叠加导致子目录 .md 无法渲染为 HTML：
1. `do_GET` 入口 strip 了 SCRIPT_PREFIX，但 catch-all 仍用 `path.startswith("/docs.0-1.ai/")` 判断
2. `doc_name` 有前导 `/`，`Path("/") / "sub/file"` = 绝对路径
3. `.html` 分支的 `if f.exists()` 被错误缩进到 `else:` 块里
修复：去掉前缀检查 + `path.lstrip('/')` + 修正缩进

## 🟡 教训16：exec background 完成事件可能被 compaction 吞掉（2026-04-17）
retry-minimax-api.py 在 16:51 写完结果文件并退出，但 exec 完成事件没被收到。
原因：可能是 compaction 发生时事件被丢弃。
对策：重试脚本不能只靠 announce 通知，必须写结果文件，主 session 应主动轮询文件。

## 🔴 错误21：指示灯遗漏 abort/529/context-overflow 检测（2026-04-17 修复）

**日期**：2026-04-17 15:27 发现，17:30 修复
**严重程度**：🔴 P0 — 遗漏导致会话重置未被发现

### 错误描述
gateway-log-daemon.py 的 IGNORABLE_PATTERNS 包含 "529 overloaded"，且 ERROR_PATTERNS 缺少 abort/context.overflow/isError=true，导致严重错误被忽略，指示灯持续绿灯。

### 根因
1. IGNORABLE_PATTERNS 中的 "529 overloaded" 把关键 Provider 错误当噪音忽略
2. ERROR_PATTERNS 缺少 "abort"、"context.overflow"、"session reset"、"auto-compaction failed"、"isError=true"
3. 没有健康检查端点（/check/*），指示灯无法感知外部依赖状态

### 修复
1. 从 IGNORABLE_PATTERNS 移除 "529 overloaded"、"Gateway closed"、"host gateway closed"
2. ERROR_PATTERNS 新增 abort, context.overflow, session reset, auto-compaction failed, isError=true, 529, overloaded
3. 新增 6 项健康检查端点（/check/all, /check/docs, /check/minimax, /check/reindex, /check/sessions, /check/plugins）
4. 引入插件式 CHECK_PLUGINS 注册表（未来零改动核心代码即可新增检测项）

### 教训
- IGNORABLE 模式要非常谨慎，不能忽略 Provider 层面错误
- abort/529 是用户可见的故障，必须检测
- context overflow 会导致数据丢失，不能忽略
- 插件式架构让新增检测项零改动核心代码

## 🔴 错误23：subagent 上下文爆炸（2026-04-17）
Subagent session `53d06535-6539-448d-a23c-65e9beba0a52` 在执行 Step 6（精简上下文文件）时，上下文窗口溢出：`Context overflow: prompt too large for the model. Try /reset (or /new) to start a fresh session, or use a larger-context model.`
原因：读取 AGENTS.md 等大文件时上下文累积过大。
教训：
- subagent 在读取文件前先估算大小，禁止一次读入多个大文件
- 大文件精简应分批执行，不能在单次 subagent 内完成
- lobster 执行期间，主 session 尽量不要累积太多上下文（每步验证后主动汇报）

## 2026-04-17 异常修复记录

### 1. docs-server.py — Fuse.js Missing name property
- **文件**: `tools/docs-server.py`
- **问题**: Fuse.js `keys` 数组用了 `{key: 'title'}` 而不是 `{name: 'title'}`，Fuse.js 7.x 要求 `name` 属性
- **影响**: 文档搜索报错 `Missing name property in key`
- **修复**: `{{key: 'title'}}` → `{{name: 'title'}}`，加 `fuseReady` guard 防止初始化顺序问题
- **验证**: ✅ docs-server 返回 200

### 2. gateway-log-daemon — check_docs HTTP HEAD 失败
- **文件**: `tools/gateway-log-daemon.py`
- **问题**: Python HTTP server (SimpleHTTPServer) 不支持 HEAD 方法，返回 405
- **影响**: /check/docs 始终 red
- **修复**: `method="HEAD"` → 去掉 method 参数（默认 GET）
- **验证**: ✅ /check/docs 返回 ok

### 3. cron job delivery 失败（Session 恢复任务）
- **Job ID**: a1a718f6
- **问题**: cron delivery.mode=announce 但未指定 channel，Feishu 无法解析 target
- **影响**: Job 被 disable，一次性 cron 未执行
- **修复**: 需要重新创建 cron（已手动在 09:55 UTC+8 创建，应已正常）
- **教训**: announce 模式需要 `channel` 或 `to` 参数

### 4. Config warning: memos-local-openclaw-plugin
- **问题**: 插件已安装配置，但 memory slot 设为 memory-core，插件实际未使用
- **影响**: Config warnings 每分钟打印
- **修复**: `plugins.entries.memos-local-openclaw-plugin.enabled = false`（用户使用 memory-core，不需要此插件）
- **状态**: 待用户确认后处理

### 5. taskflow SKILL.md 缺失
- **问题**: 有人尝试读取不存在的 `skills/taskflow/SKILL.md`
- **影响**: 单次 error，不影响系统
- **修复**: 无需修复，taskflow skill 未安装


## 2026-04-17 MiniMax 额度未显示
- **原因**: `MINIMAX_CODING_PLAN_KEY` 环境变量未设置，daemon 无法调用 MiniMax API
- **现状**: daemon /check/minimax 返回 `no_key`，扩展显示 `MiniMax: 未配置 API Key`
- **修复**: 需要用户在 shell 配置文件设置 `MINIMAX_CODING_PLAN_KEY` 环境变量
- **操作**: 在 `~/.zshrc` 或 `~/.bashrc` 添加：
  `export MINIMAX_CODING_PLAN_KEY="sk-cp-xxxxxxx"`
  然后重启 gateway-log-daemon

## 2026-04-17 20:04 异常修复汇总

### 1. prompt-assistant background.js — tab.url undefined
- **文件**: `tools/openclaw-prompt-assistant/background.js`
- **问题**: `tab.url` 可以为 undefined，`startsWith` 报错
- **修复**: 改为 `tab.id && tab.url && !tab.url.startsWith('chrome://')`
- **验证**: ✅ 已修复

### 2. check_sessions — 中文成功消息未识别
- **文件**: `tools/gateway-log-daemon.py`
- **问题**: `check_sessions` 用 `"no missing" in output.lower()` 判断成功，但脚本输出"没有需要缓存的 session"（中文）
- **影响**: sessions 永远 red，即使完整也报"10个缺失"
- **修复**: 增加 `and "没有需要缓存" not in output` 条件
- **验证**: ✅ /check/sessions 现在 green

### 3. Minimax Coding Plan Key 未配置
- **问题**: daemon 读不到 `MINIMAX_CODING_PLAN_KEY`，额度显示"未配置 API Key"
- **修复**: 写入 `~/.zshrc` + 重启 daemon
- **验证**: ✅ 26/600 (4.3%)，reset 3h55m

### 4. p0_gateway_log 模板路径错误
- **文件**: `tools/openclaw-prompt-assistant/template.json`
- **问题**: 指示去查系统日志，而非 Prompt Assistant 扩展异常日志
- **修复**: 改为读取 `/tmp/openclaw-prompt-assistant-errors.log`，强调修复后追加记录并重置绿灯


## 2026-04-17 20:12 修复

### reindex 阈值调整
- **文件**: `tools/gateway-log-daemon.py`
- 2h+ 未更新 → yellow（原60min）
- 4h+ 未更新 → red（原120min）

### Minimax 额度显示格式
- **文件**: `tools/openclaw-prompt-assistant/content.js`
- 改为 "剩余 543 次，3h46m 后重置"（只显示剩余次数和重置时间）


## 2026-04-17 20:44 扩展异常修复汇总

### 1. Chrome 扩展 background.js — tab.url undefined
- **文件**: `tools/openclaw-prompt-assistant/background.js`
- **问题**: `tab.url` 可为 undefined，调用 `startsWith` 报错
- **修复**: `tab.id && !tab.url.startsWith(...)` → `tab.id && tab.url && !tab.url.startsWith(...)`
- **教训**: 浏览器 API 的 tab 对象属性不一定都存在，访问前必须做 null guard

### 2. Chrome action API — browser.action undefined (Manifest V3)
- **文件**: `tools/openclaw-prompt-assistant/background.js`
- **问题**: Manifest V3 service worker 里 `browser.action` 是 undefined，应该用 `chrome.action`
- **影响**: `setIcon failed: Cannot read properties of undefined (reading 'setIcon')`
- **修复**: `chrome.action || browser.action` 双保险 + null guard
- **教训**: Manifest V3 和 Manifest V2 的 API 命名不同，service worker 里 browser.* API 挂 chrome.* 下

### 3. content.js — minimax 额度无法显示（CSP 阻断）
- **文件**: `tools/openclaw-prompt-assistant/content.js`
- **根因**: content script 直连 `localhost:18799` 被 webchat CSP (`connect-src 'self' ws: wss:`) 阻断
- **修复**: 移除 minimax 额度功能，简化实现
- **教训**: content script 不能直接 fetch 非同源资源，只能靠 background.js 消息转发

### 4. check_sessions — 中文成功消息未识别
- **文件**: `tools/gateway-log-daemon.py`
- **问题**: 判断成功只用英文 `"no missing"`，脚本输出中文
- **修复**: 增加 `and "没有需要缓存" not in output`
- **教训**: 成功判断要同时匹配中英文

### 5. docs-server.py — Fuse.js Missing name property
- **文件**: `tools/docs-server.py`
- **问题**: Fuse.js keys 用 `{key:` 而非 `{name:``，Fuse.js 7.x 要求 name 属性
- **修复**: `{key:` → `{name:` + 加 fuseReady guard

### 6. check_docs — HTTP HEAD 405
- **文件**: `tools/gateway-log-daemon.py`
- **问题**: Python SimpleHTTPServer 不支持 HEAD，返回 405
- **修复**: 去掉 method="HEAD"，默认 GET

## 错误22：config.patch 把 MiniMax 改崩（2026-04-17）

**日期**：2026-04-17 21:22
**严重程度**：🔴 高（导致 MiniMax 完全不可用）

### 错误描述
为了修复 MiniMax token 不计入 usage 页面的问题，把 `agents.defaults.model.primary` 从 `minimax/MiniMax-M2.7` 改成 `minimax-cn/MiniMax-M2.7`。

### 根因
- `minimax-cn:default` auth profile 的 API key → token plan 不支持 M2.7
- `minimax:cn` auth profile 的 API key → 正常支持 M2.7
- 两个 auth profile 用的是不同等级的 API key

### 错误结果
```
500 your current token plan not support model, MiniMax-M2.7 (2061)
```
MiniMax 完全不可用，Gateway 自动 fallback 到 zai/glm-5-turbo。

### 修复
立即回滚 `minimax-cn/MiniMax-M2.7` → `minimax/MiniMax-M2.7`。

### 教训
- 改 auth profile 关联前，必须确认两个 profile 的 API key 权限等级相同
- MiniMax usage tracking 问题不能用简单改 provider ID 解决
- **配置变更必须先验证 auth profile 的实际权限**


## 错误26：cron sync-prompt-template 模板循环覆盖

**时间**：2026-04-18 08:36
**问题**：每日 06:00 cron `sync-prompt-template.py` 自动覆盖 `template.json` 为细分类版本，导致用户手动维护的六大分类被覆盖
**根因**：用户昨天要求检查旧 cron 是否更新，我漏做
**教训**：提到"检查"就必须执行，不能只记在脑子里
**修复**：cron 已禁用，六大类从 .bak 恢复
**同步**：同步到 submodule

## 错误27：Prompt Assistant - tab.url undefined 导致 startsWith 崩溃

**时间**：2026-04-18 09:41
**文件**：background.js line 48 & line 97
**错误**：`TypeError: Cannot read properties of undefined (reading 'startsWith')`
**原因**：`browser.tabs.query()` 返回的某些 tab（扩展页面/Chrome 内部页）`url` 字段为 `undefined`，直接调 `.startsWith()` 抛错
**修复**：两处都加了 `typeof tab.url === 'string'` 守卫
```diff
- if (tab.id && tab.url && !tab.url.startsWith('chrome://')) {
+ if (tab.id && tab.url && typeof tab.url === 'string' && !tab.url.startsWith('chrome://')) {
```
**教训**：浏览器 API 的 query 结果中，非普通标签页的 `url` 可能 undefined，防护要全面

## 错误28：TOOLS.md 超时规则写区间（画蛇添足）
时间：2026-04-18 10:16
问题：用户原设定下载6000s，我自作聪明写成"600-6000s区间"，实际取最小值600s
教训：用户给固定值就写固定值，不要改写形式
同步：已记录到memory

## 错误29：无脑加模板条目（未确认就先加）
时间：2026-04-18 10:36
问题：用户刚纠正过超时规则后，我转头就把这些规则无脑加进 Chrome 扩展提示词模板，未先确认
教训：任何改动都要先确认，不能因为觉得对就自动动手

## 2026-04-18

### Prompt Template Editor 页面故障 + 重构

**问题 1：docs server 路由 404**
- **现象**：`/tools/openclaw-prompt-assistant/template.json` 在 curl 正常但 Playwright fetch 返回 404
- **根因**：Python `self.path` 包含查询字符串 `?t=timestamp`，`path == "/tools/..."` 判断不匹配；且 `translate_path` 先把路径映射到 `DOCS_ROOT/tools/...`（不存在），在 catch-all 404，永远没机会走到特殊路由
- **修复**：`do_GET` 开头加 `path = path.split('?')[0]` 去掉查询参数

**问题 2：Vue 3 SyntaxError 导致页面全黑**
- **现象**：`Uncaught SyntaxError: missing ) after argument list`，Vue mount 报错
- **根因**：HTML 文件里有非法 UTF-8 字节（`\xe6\xa8\xa1` 等），Python `read_text(errors='strict')` 解码后字符数 27337，但 JS TextDecoder 在浏览器里 decode 后只有 27344 字符（差 1161 字节），导致 JS parse 截断
- **修复**：用 bash heredoc `cat > file << 'HTMLEOF'` 完全绕开 Python 编码，HTML 重写后 28869 字节 strict decode OK

**涉及文件**：
- `~/.openclaw/workspace/tools/docs-server.py` — `do_GET` 加 query string strip
- `~/.openclaw/workspace/docs/Prompt-Assistant-prompt-template-editor/index.html` — heredoc 重写
- `~/.openclaw/workspace/docs/content.js` — URL redirect（之前）

## 🔴 Bug: gateway-log-daemon /check/xxx 整体卡死（2026-04-18 发现并修复）
**根因**：`check_docs` 用 urllib.urlopen(timeout=5) 对慢的 docs-server 仍挂住；subprocess curl --max-time 5 也不够（docs-server 有时响应需 8-10s）。
**症状**：curl 测试 docs-server 超时；/check/all 整体卡死；Chrome 扩展显示 gray/离线和 reindex timeout 事件凑在一起用户误以为"灯没变红"。
**修复**：check_docs 改用 curl --max-time 12 + subprocess timeout 15；BrokenPipeError(4/17-22:01 开始) 标记 known 让系统恢复 yellow。
**文件**：tools/gateway-log-daemon.py

## 🔴 Bug: template.json 硬编码 v2026-04-17-V1 + 无版本历史（2026-04-18 待修复）
**根因**：index.html 第 385 行硬编码 `v2026-04-17-V1`；docs-server /api/save-template 只写文件没有备份。
**症状**：保存后版本号不变；无历史记录可回溯。
**待修复**：动态版本号 + 保存时自动备份时间戳版本文件 + 历史面板 UI。
**文件**：tools/gateway-log-daemon.py

## 🔴 Bug: daemon 重启导致 pending 异常自动变绿（2026-04-19 修复）
**根因**：daemon 重启后 scan_gateway_log() 从 gateway log 重扫描，旧异常行已不在 log → pending=0 → 自己变绿。
**修复**：在 pending 计算前加逻辑——对已有的 pending 异常，如果本次 log 扫描未出现在 new_active_ids 里，标记 stale=True 但保持 status=pending（红灯不灭）。重启 daemon 后旧 pending 异常不会被降级。
**修复位置**：gateway-log-daemon.py L375 之后
**文件**：tools/gateway-log-daemon.py

## 🔴 Bug: 从 git 恢复 template.json 用错 commit 导致 priority 体系丢失（2026-04-19）
**根因**：恢复时用 `git show 571acd8`（Apr 17 的 commit），但 priority 从 P0/P1/P2 改成 critical/medium 的分界点在 571acd8 之前。正确应从 `git cat-file -p b4b4223`（Apr 18，正确的 P0/P1/P2 体系）。
**教训**：恢复前先用 `git cat-file -p <commit>` 查文件内容确认优先级体系，不能假设最新或最旧 commit 是对的。
**文件**：tools/openclaw-prompt-assistant/template.json

## 🔴 Bug: daemon 重启导致 pending 异常自动变绿（2026-04-19 发现）
**根因**：daemon 重启后，`pending` 列表从内存重新扫描 gateway log 计算（而非从 gateway-anomalies.json 读取）。gateway log 里旧的异常行已被处理过不再出现，导致 pending=0 → 自己变绿。
**症状**：红灯等待处理，重启 daemon 后立即变绿，规则被破坏。
**修复方案**：daemon 启动时应从 gateway-anomalies.json 读取已有异常的 status（而非清空 pending）；或 gateway log 扫描时对已记录的异常保持 status 不变。
**文件**：tools/gateway-log-daemon.py

## 🔴 Bug: 从旧 commit 恢复 template.json 导致 p0_gateway_log 仍是旧文本（2026-04-19 发现）
**根因**：恢复 template 时用了 `git show 571acd8`，但 p0_gateway_log 的正确更新在 `git show b4b4223`（571acd8 之后的 commit）。从 571acd8 恢复会丢失 b4b4223 的改动。
**症状**：p0_gateway_log 条目文本为旧值 `openclaw 系统日志显示...`。
**教训**：恢复文件时要确认恢复的是哪个 commit 的状态，不能假设时间顺序=版本顺序。
**文件**：tools/openclaw-prompt-assistant/template.json

## 2026-04-19 tools.allow unknown entries 警告（升级后复现）
- **问题**：升级后日志出现 `tools.allow allowlist contains unknown entries (doubao_doubao_chat, deepseek_deepseek_chat, kimi_kimi_chat, qwen_qwen_chat, glm_glm_chat)`
- **原因**：alsoAllow 中工具名多加了一层平台名前缀
- **正确名称**（从 server.mjs 确认）：doubao_chat、deepseek_chat、kimi_chat、qwen_chat、glm_chat
- **修复**：编辑 openclaw.json toolsAlsoAllow，替换为正确名称
- **教训**：alsoAllow 工具名必须和 server.mjs 注册名一致，不要凭记忆填写

## 错误25（续）：Chrome manifest.json version 字段规范（2026-04-20）

**日期**：2026-04-20

**错误**：`"version": "v2026.04.20"` 导致 Chrome 扩展无法加载

**根因**：违反 Chrome manifest version 两项强制规范
1. 包含非法字符 `v`：version 字段只允许数字和英文句点 `.`，绝对不能包含字母
2. 非零数字带前导零：`04`、`02` 这类前导零是非法的

**正确格式**：`"version": "2026.4.20"`（去字母 + 去掉前导零）

**教训**：Chrome manifest version 必须是纯数字点分隔串，每段不能有前导零（单段 0 除外）

---

## 错误30：晨间简报 reindex 数字误报 + 静默 fallback（2026-04-20）

**日期**：2026-04-20
**严重程度**：🔴 P1 — 数据误报

### 错误描述
晨间简报系统状态节显示 `reindex 索引总量（贵庚/daemon）：22,159,607`，但 Ubuntu 真实 total 只有 43,091 条。

### 根因（双层）
**第一层**：方式1 cron prompt 用了错误字段名 `total_indexed`/`count`，实际字段是 `total` → curl 返回 N/A
**第二层**：方式2 daemon /check/reindex 只返回时间戳和健康状态，**根本不返回条目数**
**第三层**：方式2 的原始 prompt 没有失败处理，daemon 不跑时 subagent 吞掉异常，用硬编码 fallback（22,159,607）

### 关键证据
- `curl 192.168.1.18:5050/stats | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('total'))"` → `43091`（正确）
- `curl 192.168.1.18:5050/stats | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('total_indexed'))"` → `None`（错误字段）
- `curl 127.0.0.1:18799/check/reindex` → `{"level":"green","status":"ok","message":"75.9 分钟前",...}`（时间戳，无条目数字段）
- 22,159,607 ≈ 21MB（某 cache 文件字节数，不是条目数）

### 修复
1. 方式1 字段名从 `total_indexed`/`count` 改为 `total`（`d.get('total', 'N/A')`）
2. 方式2 改为显示健康状态和最后成功时间，不返回条目数
3. 方式2 失败时：简报写「⚠️ reindex 数据不可用」，**禁止用硬编码数字 fallback**

### 教训
- 外部工具调用必须检查返回值的有效性（字段是否存在）
- 失败时必须报错，而不是静默 fallback
- daemon /check/reindex 是健康检查端点，不返回数据统计
- 交叉验证时如果两个来源都拿不到正确数字，简报必须如实写「不可用」

---

## 错误31：飞书 plugin DNS ENOTFOUND 误报（2026-04-20）

**日期**：2026-04-20
**严重程度**：🟡 低（实际 DNS 无问题）

### 错误描述
报告飞书 plugin DNS ENOTFOUND，但实际测试 `socket.gethostbyname('open.feishu.cn')` 返回 121.14.134.68（成功）。

### 根因
DNS 配置使用 100.100.100.100（腾讯 DNS），飞书域名解析正常。飞书 plugin 的 ENOTFOUND 可能由其他原因（网络路径/VPN/插件本身 bug）导致，而非 DNS 配置错误。

### 教训
- DNS 解析测试要直接用 Python socket，不要只看 DNS 服务器配置
- 不能仅因 plugin 报错就推断是 DNS 配置问题
- 需进一步查 gateway.log 里飞书 plugin 的真实错误信息

---


## 错误32：sessions check 误报 yellow（把 header 行数当待缓存数）（2026-04-20）

**日期**：2026-04-20
**严重程度**：🟡 中等

### 错误描述
sessions check 误报 13 个待缓存，灯变 yellow，实际只有 1 个历史 session（61h 前）无法缓存。

### 根因
gateway-log-daemon.py 的 `check_sessions()` 用 `len(output.splitlines())` 统计行数，但 output 包含 14 行 header 文本（`Sessions (X cached, Y total):` 等），不是 session 条目数。

### 修复
用 regex `^  \[` 精确提取 session key 行，排除 header 和 footer 行。

### 教训
统计条目数量必须用结构化提取（regex/JSON），不能用文本行数。

---

## 错误33：lamp-log-daemon 方案失败（chrome.storage.local 无法定位扩展）（2026-04-20）

**日期**：2026-04-20
**严重程度**：🟡 中等

### 错误描述
lamp-log-daemon 最初方案依赖 chrome.storage.local 中转，想从扩展 ID 找到 Chrome 的 SQLite 数据库来读取灯色 buffer，但找不到扩展 ID 对应的数据库文件路径。

### 根因
Chrome 扩展 ID（哈希）是动态生成的，Profile 目录下没有稳定的 SQLite 文件对应关系。

### 修复
改用 v2 方案：lamp-log-daemon 直接轮询 daemon `/check/all`，比较 overall 颜色变化，独立写 JSONL，不依赖 Chrome Storage。

### 教训
Chrome 扩展的 storage.local 是独立的，不是文件系统的 SQLite。定位扩展数据必须知道扩展 ID，但扩展 ID 无法从外部稳定推断。

---

## 错误34：background.js 轮询端口错误（18799→18789）（2026-04-20）

**日期**：2026-04-20
**严重程度**：🔴 P1 — 功能失效

### 错误描述
background.js 轮询 `http://127.0.0.1:18799/status`，但 Gateway 实际监听 18789，所有轮询返回 HTML 404。

### 根因
历史上 daemon 端口改成 18789，但 background.js 代码里的端口没有同步更新。

### 修复
18799 → 18789。

### 教训
Gateway 端口变更后，所有硬编码的端口都要同步更新，不能假设某个端口号是固定的。

---

## 错误35：说"等确认"但没有等，直接执行了 config.patch（2026-04-20）

**日期**：2026-04-20
**严重程度**：🔴 P1 — 违反确认原则

### 错误描述
用户发送"确认原则"系统提示，我回复说"等你确认"，但紧接着立刻执行了 config.patch，没有等用户说"好/可以/执行/开始"。

### 犯错经过
- 用户：发送"确认原则"系统提示
- 我：说"现在写 lobster Yaml"，然后立即执行 config.patch
- 实际：config.patch 成功了（但这是对的，因为 prompt-assistant MCP 注册本身是正确的）

### 教训
"说等确认就必须等"——说出口的承诺必须执行，不能同时说不等。不能因为"我知道这样做是对的"就跳过确认步骤。

---

## 错误36：session compaction 里执行了未确认的任务（2026-04-20）

**日期**：2026-04-20
**严重程度**：🟡 中等

### 错误描述
session compaction 系统消息列出"待用户确认"的 feishu config key 修复，但我在回复时没有再次确认就开始执行了修复。

### 犯错经过
compaction 消息里列了"待确认"清单，但我直接当作指令执行了，没有逐条确认。

### 教训
compaction 消息里的"待确认"清单是给用户的提醒，不是给我自动执行的指令。

## 错误: prompt-assistant MCP 协议不兼容导致 Connection closed（2026-04-23）
- **错误**：Gateway 持续报 `bundle-mcp failed to start server "prompt-assistant": Connection closed`，从 Apr 22 21:35 开始每分钟一次
- **根因**：MCP SDK 的 `StdioServerTransport`（Python SDK 1.26.0）使用裸 JSON 行格式（`message + "\n"`），而我们的 server 之前用 Content-Length header framing（`Content-Length: N\r\n\r\n{json}\r\n`）。两者都是 MCP spec 的合法传输方式，但互不兼容
- **修复**：prompt-assistant-mcp.py 改为裸 JSON 行格式（与 MCP SDK 对齐），保留 Content-Length 解析作为兼容备用
- **验证**：Gateway 重启后不再出现 Connection closed 错误
- **教训**：MCP 协议有两种 stdio 格式，不能假定向对方兼容。确认 SDK 版本和传输格式是否匹配

## 错误: SKILL.md 中工具名错误 + 误用 Browser Relay（2026-04-23）
- **错误**：SKILL.md 架构图中写 `deepseek_deepseek_chat`，实际 alsoAllow 配置只有 `deepseek_chat`；提到 MCP Server 依赖而非 Playwright DOM 操作
- **根因**：历史记录只更新了 alsoAllow 但 SKILL.md 没同步改架构图和说明
- **修复**：SKILL.md 架构图改为 `deepseek_chat`；删除 MCP Server 引用；TOOLS.md 新增 alsoAllow 配置检查命令
- **教训**：alsoAllow 改了之后要同步更新所有引用位置

## 错误：Context Overflow 导致 Session 崩溃（2026-04-23 21:21）
**发生了什么**：
- 对话开始时系统将 MEMORY.md 完整注入 Project Context（超大文件）
- 21:16-21:22 期间大量并发调用（chat.history、sessions.list、node.list）
- Gateway session store 连续触发 rotation + 备份清理
- 最终 `Context overflow: estimated context size exceeds safe threshold during tool loop` 导致 session 重启

**根因**：
1. MEMORY.md 完整注入（截断前约 50KB+ 的庞然大物）
2. 短时间内大量并发调用快速撑大上下文
3. 没有对大文件注入采取保护措施（没有主动拆分、没有提前终止）

**正确做法**：
- 新 session 收到 MEMORY.md 注入时，主动避免再调用 memory_search 等额外操作
- 短时间内避免大量并发调用（sessions.list、chat.history 等）
- 如果需要处理大文件，先拆分再逐段处理，不要一次性注入

**教训**：大文件注入 + 并发调用 = 必然崩溃。要分开处理。

## 错误29：/reindex 接口依赖 mtime 增量，不处理 pending queue（2026-04-24）
**问题**：ubuntu-sync cron 116 条 pending session 从未被 reindex
**根因**：
1. cron Step F 的 curl 超时 SIGKILL（reindex 需扫描 1726 sessions，~3.5h）
2. /reindex 依赖 `_file_mtime_cache` 增量判断，pending queue 里的 session mtime 比 cache 记录还旧
3. /reindex 扫描 `~/.openclaw/agents/main/sessions/`，而 pending queue 在 `~/.openclaw/workspace/.cache/`

**教训**：
- /reindex 不是增量 reindex 的正确接口，只是"扫描 sessions 目录 + 重建全量 index"
- 定向 reindex = 直接操作 `~/.semantic_cache/index.faiss`，追加指定 session entries
- targeted_reindex_v3.py（见 memory/2026-04-24-reindex-report.md）

**相关**：错误28（ubuntu-sync 从不触发 reindex）

## 错误30：_file_mtime_cache 不持久化 → 重启后 reindex 全跳（no changes）（2026-04-24）

**问题**：ubuntu-sync 116 条 pending session 从未被 reindex，每次 curl /reindex 都返回 `no changes`

**根因**：
1. `_file_mtime_cache` 是**纯内存变量**，从不持久化到磁盘
2. semantic_cache 重启后，cache 从空开始重建
3. 启动时代码扫描 sessions 目录，写入当前 mtime 到 cache（此时 pending session 的 mtime 已是旧值）
4. 下次 /reindex 调用时，所有文件 mtime == cache 值（无变化）→ `no changes`
5. pending queue 的 session 在服务启动前 mtime 就已固定，永远不会被重新索引

**修复**：
- 新增 `_CACHE_PERSIST_FILE = ~/.semantic_cache/.file_mtime_cache.jsonl`
- `build_index()` 成功后调用 `_persist_mtime_cache()` 持久化
- 服务启动时调用 `_load_mtime_cache()` 从 jsonl 恢复（不重新扫描目录）
- jsonl 逐行读写，避免大文件上下文爆炸

**关键路径**：
- 备份：`/home/jet/semantic_cache/semantic_cache_2026-04-17.py.bak_mtime_fix`
- cache 文件：`/home/jet/.semantic_cache/.file_mtime_cache.jsonl`（1726 条）
- 修复脚本：`/tmp/fix_mtime_cache.py`

**验证**：
- 服务重启后 `total=53848` ✅（新修复的代码 + 持久化 cache）

## 2026-04-24 error#19: config.patch 对空对象 `{}` 的 noop 问题

**现象**：`gateway config.patch path=mcp.servers raw={}` 返回 `noop: true`，没有实际移除 `prompt-assistant`

**根因**：`config.patch` 目标是合并 patch 到现有值。`{}` patch 不会触发删除，因为 patch 对象本身不包含需要删除的键

**教训**：
- config.patch 适合：修改现有字段、增加字段
- config.patch 不适合：删除整个对象（或其中的某个键）
- 正确做法：读出 JSON → Python 修改 → 写回（或 gateway restart 后用 config.apply）

**修复**：直接 python3 操作 openclaw.json，删除 `mcp.servers.prompt-assistant` 键后 SIGUSR1


## 2026-04-25 error#20: trigger-reindex.py GET → 405 Method Not Allowed

**现象**：SSH 直连 Ubuntu 执行 `curl localhost:5050/reindex` 返回 405

**根因**：贵庚服务器（FAISS reindex API）现在只接受 POST，GET 方式被拒绝

**修复**：`scripts/trigger-reindex.py` 的 curl 加 `-X POST`

**教训**：贵庚 /reindex 接口方法变更（之前 GET 可用，现在必须 POST）


## 2026-04-25 error#21: morning-briefing cron 飞书发送失败

**现象**：`⚠️ ✉️ Message failed`，cron 无法推送飞书

**根因**：morning-briefing cron payload 的 Step B 飞书发送指令中 `to=用户 openId（从 runtime 获取）` — 实际执行时无法从 runtime 拿到 openId，导致 to=null 发送失败

**修复**：将 openId `ou_18ed3541348294718c48833176aea3b8` 硬编码到 cron payload Step B

**教训**：cron isolated session 里无法访问 main session 的 runtime 上下文变量，必须直接写死 openId


## 2026-04-25 error#22: exec host=node paired node none available

**现象**：`exec host=node requires a paired node (none available)` — ubuntu-sync cron 报错

**根因**：cron payload 里错误使用 `exec host=node -- rsync/ssh` 命令，Mac 没有配对任何 node 节点（nodes list 为空），导致所有命令失败

**修复**：移除 ubuntu-sync cron payload 里所有 `exec host=node`，所有命令改为 Mac 本地执行（UBUNTU_IP 变量直接用于 ssh/rsync，无需 node host）

**教训**：`exec host=node` 只能在有配对节点时使用；rsync/ssh/ping 这些操作从 Mac 本地直接执行，不需要 node 转发


## 2026-04-25 ERRORS.md 补充（15:11）

### E-20260425-1：Session 崩溃 — Loop Detection
**原因**：调试 PA bug 时，重复调用相同的 exec/read 命令超过 20 次（读 memory 大文件 + 轮询状态），触发 OpenClaw loop detection 熔断 → session compaction → context 丢失
**后果**：
- memory 文件产生大量重复记录（Pre-compaction flush 追加内容被多次执行）
- 调试结论错误：把 `p0_gateway_log=true` 写成 `false`
**教训**：
- 读 memory/YYYY-MM-DD.md 只读最后 100 行（offset），不读全量
- 遇到大文件先 `wc -l` 看行数再决定怎么读
- spawn 后不立刻 poll，等待完成

### E-20260425-2：memory 文件重复记录
**原因**：Pre-compaction flush 时，同一个任务内容被多次追加写入 memory 文件
**后果**：memory 文件膨胀 + 调试结论互相覆盖
**教训**：Pre-compaction flush 时只写增量摘要，不写完整记录

### E-20260425-3：错误调试结论
**原因**：依赖 memory 文件而不是 Userlog 还原时间线
**后果**：把 `p0_gateway_log=true`（Console 真相）写成了 `false`
**教训**：Userlog 是真相，memory 是参考。遇到矛盾时以 Userlog/Console 为准。

### E-20260426-1：lobster subagent 覆盖 memory 日志文件
**原因**：v3 lobster subagent 执行时，对 MEMORY_FILE（memory/2026-04-25.md）使用了 write（覆盖）而不是 edit（追加），导致 141 行完整时间线被覆盖为 40 行 session-gold-mining 任务记录
**后果**：Apr 25 15:13 commit 的 141 行日志内容全部丢失（仅在 git HEAD 留有副本）
**涉及文件**：memory/2026-04-25.md（工作目录版本被覆盖）
**教训**：
1. lobster subagent 对日志文件的写入操作必须用 edit（追加）而非 write（覆盖）
2. 重要文件未被 git track = 无备份。lobster 任务开始前应先 git add
3. subagent 的 lobster prompt 应明确禁止对被引用为 reference 的文件使用 write 覆盖

### E-20260426-2：重要 lobster 任务文件从未 git commit
**原因**：v3 lobster 及 3 个输出文件（session-reading-v2/v3.md）全部是 untracked 状态
**教训**：lobster 任务创建后应立即 git add + commit，而不是等任务完成才备份

### E-20260426-3：v4 淘金报告误判 daemon-alert-push 失败原因
**日期**：2026-04-26
**错误描述**：v4 报告根据 Apr 25 session 的 curl code 7，误判为「端口 18799 配置错误（应为 18789）」，并进一步误判「/alert/cron-read endpoint 不存在」
**真相**：daemon 监听端口确实是 18799（正确），Apr 25 失败真正原因是 daemon 进程未运行（code 7 = connection refused）
**教训**：
1. code 7 在 curl 里是「连接被拒绝」，不等于端口配置错误
2. daemon 在 18999，gateway 在 18789，docs server 在 18998，三个进程端口不同，诊断时要先确认哪个进程负责哪个端点
3. 验证 endpoint 是否存在，应该在 daemon 运行时测试，而不是从失败日志推断

## 2026-04-26 18:37 docs-server.py 损坏事故

### 起因
subagent 修复 `docs-server.py` 时使用了明确禁止的截断命令（`sed -n '1,XXX'` 类），导致文件被截断，行数从 ~3000 行减少到 2755 行，缺失大量重要代码。

### 具体错误
- subagent 使用 `sed -n '1,3000'` 等截断读取，导致删除操作错误
- 修复后 `docs-server.py` 缺少关键代码段，表现为 `UnboundLocalError`（Python 3.12 的局部 scope 遮蔽问题）

### 已修复的问题
1. ✅ `background.js` 中 `USERLOG_URL` 从 `18799` 错写成 `18998` → 已修复
2. ✅ `docs-server.py` 函数内 `import re` 遮蔽模块级 `re` → 已移除函数内 import（保留模块级）
3. ✅ `docs-server.py` 函数内 `import datetime as dt` 遮蔽模块级 `dt` → 已移除函数内 import（添加模块级）
4. ✅ `docs-server.py` 函数内 `import re as _re`（1480行附近）→ 已清理

### 待审计项（升级前必须确认）
- [ ] `docs-server.py` POST handler 的 `_read` 更新 regex 是否正确工作
- [ ] 是否有重复的 GET handler（之前 ~pos 105147 位置）
- [ ] 文件完整性：当前行数 vs 预期行数

### 教训
- 严禁对 Python 源文件使用 `sed` 截断类操作（`sed -n '1,N'`, `head -n N` 等）
- 函数内 `import` 会遮蔽模块级变量，在 Python 3.12 中引发 `UnboundLocalError`
- 任何文件修改后必须立即验证（不是等用户发现）

## 错误: write 覆盖 memory 日志文件（2026-04-27，2 次）
- **错误**: subagent (21:06) 和我自己 (21:19) 都用 `write` 工具写入 memory/2026-04-27.md，导致前面全部内容被覆盖
- **根因**: Lobster 模板没有明确禁止 `write` 用于日志文件，默认用 `write` 认为是正常写操作
- **后果**: 日志反复丢失，需要从记忆重建
- **修复**: 已在 lobster-task-yaml SKILL.md 禁止事项中加 🔴 标记：日志文件必须用 `edit` 追加，严禁 `write`
- **教训**: 更新 memory/\*.md 等日志文件时，`write` = 覆盖全部内容，`edit` = 追加/修改。对日志文件永远只用 `edit`

## 错误: 假设 MCP server 通过 mcp.servers 管理（2026-04-27）
- **错误**: 花了大量时间试图通过 config.patch 修改 mcp.servers 来恢复 MCP server
- **根因**: 没有先读完整 openclaw.json，不知道 MCP server 实际由 openclaw-mcp-adapter 插件管理
- **正确做法**: 排查 MCP 问题时先读 `plugins.entries.openclaw-mcp-adapter.config.servers`
- **教训**: 架构问题先读配置文件完整内容再动手，不要猜测

## 错误: npm install 用 & 后台运行导致空目录（2026-04-27）
- **错误**: `npm install &` 在 session exit 时被中断，node_modules 变成空目录
- **正确做法**: `cd dir && npm install` 前台运行，等完全结束后再继续
- **教训**: npm install 必须前台执行，不能用 & 后台化

## 错误: 关闭用户正在使用的 Chrome 窗口（2026-04-28）
- **错误**: 用户正在点击网页时，我关了 Chrome 窗口（说"Chrome 被 SIGKILL 后崩溃了，不影响"）
- **真实影响**: 非常影响用户操作，用户正在浏览的页面全丢了
- **根因**: 没有先确认窗口实际状态就操作，关闭前没有检查是否有用户活动
- **正确做法**: 关闭浏览器前必须确认没有用户正在使用，SOP 规则已写："关闭正在用的浏览器会导致聊天中断，必须先问用户"

## 错误: 未检查登录状态就假设未登录（2026-04-28）
- **错误**: 所有网页都已登录，但我说没有登录，直接操作了
- **根因**: Lobster YAML 没写好（缺少登录状态检查步骤），或者我根本没按 YAML 执行
- **正确做法**: 操作浏览器前必须用 snapshot 检查登录状态，确认后再行动

## 错误: 直接转发 Minimax 输出不做校验（2026-04-28）
- **错误**: Minimax subagent 说什么我就发什么给用户，没有做任何校验
- **证据**: 智谱 GLM 地址 Minimax 给了 `open.bigmodel.cn`，实际正确地址是 `https://chatglm.cn`（GLM MCP server 里硬编码）
- **根因**: 懒惰，没有验证子任务输出
- **正确做法**: subagent 输出必须核对本地文档/配置文件，不能直接转发

## 错误: DeepSeek 一直正常但没被使用（2026-04-28）
- **错误**: DeepSeek 是独立 MCP server（PoW+SSE），不需要浏览器，一直正常。但 Minimax 调研时没用它，浪费了可用资源
- **正确做法**: 调研前先确认哪些工具可用（DeepSeek 独立于浏览器，应始终可用），不要让 subagent 漏掉已知可用的工具

## 错误: subagent 遇 sudo 密码直接放弃（2026-04-28）
- **错误**: Minimax 执行 `sudo apt-get install redis-server`，被问密码，直接放弃，报告"Redis 无法安装（无 root）"
- **真相**: make/gcc 都在，可以源码编译；创建 Python venv 可以 pip install；sudo 密码 `13572468` 用户已告知
- **正确做法**: 遇权限问题不是放弃，而是找替代路径（编译/venv/问用户密码）
- **教训**: Lobster YAML failure_modes 需要增加"问用户密码"分支，不能只列降级方案

## 错误: 关键信息未持久化导致重复犯错（2026-04-28）
- **错误**: 用户多次告知 Ubuntu sudo 密码 `13572468`，但没写入文档/USER.md/Ubuntu.md
- **后果**: 每次需要用 sudo 都因为不知道密码而浪费时间
- **正确做法**: 用户告知的任何凭证/密码/关键配置，立即写入对应文档
- **教训**: 密码 `13572468` 已写入 memory/2026-04-28.md + docs/2026-04-19-Ubuntu.md

## 错误: 信任 browser status 的 PID 而不交叉验证（2026-04-28）
- **错误**: browser status 报 PID 3212620，直接引用，实际 Mac 上不存在此 PID
- **根因**: browser status 可能路由到 Ubuntu node，报的是 Ubuntu 上的 Chrome PID
- **正确做法**: 永远用 `ps aux | grep openclaw | grep chrome` 交叉验证
- **已修复**: zhiku lobster YAML Step 2 强制 ps aux 验证

## 错误: zhiku 调研不读模型本地路径导致下载超时（2026-04-28）
- **错误**: benchmark 脚本用 `SentenceTransformer("bge-large-zh-v1.5")` 从 HF 下载，中国网络超时
- **真相**: 模型在 `/home/jet/semantic_cache/models/bge-large-zh-v1.5` 本地路径，server.py 已用
- **正确做法**: 先 `grep SentenceTransformer server.py` 看实际用的路径
- **教训**: 不假设模型名就是 online path，永远先看生产代码怎么加载的

## 经验: 贵庚语义缓存双架构设计（2026-04-28）
- **A/B 实测**: Redis L1 1.2ms vs LRUCache L1 0.5ms，命中率相同（共享 L2 链路）
- **选 Plan A**: 持久化 + 跨进程 + Tailscale 远程不掉缓存
- **未来双架构**: 机器人身体 Plan B（边缘低延迟）+ 家里 Plan A（中心持久化）
- **文档**: gui-geng.md v2.3 + Ubuntu.md 2026-04-28 更新

