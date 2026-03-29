# Deep Research 工具状态检查 SOP

> 本 SOP 由 2026-03-24 教训总结。MiniMax 在工具状态检查时反复犯同一个错误，因此必须写得极度详细，确保明天重新读时能原样重现。

---

## 目的

在开始任何深度调研之前，验证所有工具的实际可用性。
**不是**检查"页面能不能打开"，而是检查"工具本身能不能调通"。

---

## 常见错误（必须避免）

| 错误做法 | 为什么错 |
|---------|---------|
| 用 Playwright 打开 5 个 AI 网页，看页面加载就算"检查通过" | 页面能加载 ≠ MCP Server 能用 ≠ 登录凭证有效 |
| 用 `textContent('body')` 搜索"登录"文字判断登录态 | 文字可能出现在无关位置，检测不准确 |
| 只检查 Chrome CDP 能不能连，不检查每个 webauth 工具 | CDP 连通 ≠ 工具可用 |
| 凭记忆说"工具都正常"而不实际调用 | Token 可能已过期，必须实际调用验证 |
| 用 `thinking=false` 代替实际思考模式 | `thinking=true` 才能验证深度思考功能是否正常 |
| 遇到报错就慌张反复重试 | 报错 ≠ 失败，应先验证（curl 测一下）再决定是否重试 |
| mdview 端口占用时连续执行多次 | 可能第一次已经成功了，反复执行会打开多个重复标签页 |
| 修复问题时反复换方案，不先分析根因 | 最简方案往往最有效，过度设计浪费大量时间 |
| daemon 线程中用 `sys.exit` 退出 | `sys.exit` 只退线程不退进程，必须用 `os._exit` 强杀 |

---

## 操作步骤

### Step 1：检查 Chrome CDP（基础依赖）

**命令：**
```bash
curl -s --max-time 3 "http://127.0.0.1:18800/json/version"
```

**期望结果：** 返回 JSON 包含 `Browser` 字段

**判断：**
- ✅ 返回 JSON → Chrome CDP 正常
- ❌ 超时或无响应 → OpenClaw 托管浏览器未启动，**停下来问用户**

---

### Step 2：直接调用 5 个 webauth 工具（核心步骤）

**必须逐个直接调用工具本身，不是打开页面。**

给每个工具发送同样的测试消息：`"OK"`（或 `"你好"`）

**调用方式：** 使用对应的 webauth 工具函数（参考下方完整列表）

**5个工具的调用命令（串行或并行均可）：**

```
1. doubao_doubao_chat(message="OK", thinking=true)
2. kimi_kimi_chat(message="OK", thinking=true)
3. glm_glm_chat(message="OK", thinking=true)
4. qwen_qwen_chat(message="OK", thinking=true)
5. deepseek_deepseek_chat(message="OK", thinking=true, search=false)
```

**注意**：`thinking=true` 是为了验证平台深度思考功能正常。如果某个平台不支持 `thinking` 参数，忽略即可。

**期望结果：** 每个工具在 30 秒内返回正常回复（非错误、非空）

**判断：**
- ✅ 收到正常回复（文字内容正常）→ 工具正常
- ❌ 超时（>30秒无响应）→ MCP Server 或登录凭证过期
- ❌ 返回 `MCP error`、`bad request` 等错误 → 需要修复

**重要：** 响应时间也要记录。如果一个工具平时 3 秒突然变成 20 秒，要标记 ⚠️。

---

### Step 3：搜索工具

**minimax search：**
```bash
cd ~/.openclaw/workspace && python3 skills/minimax-tools/minimax.py search "test"
```
- ✅ 返回搜索结果
- ❌ 报错

**tavily search：**
```bash
python3 skills/tavily-search/search.py "test" 1
```
- ✅ 返回搜索结果
- ❌ 报错

**Brave web_search：** 已知无 API Key，跳过（用 minimax search 替代）

---

### Step 4：subagent

```javascript
sessions_spawn(
  task="回复：OK",
  runtime="subagent",
  mode="run",
  runTimeoutSeconds=30
)
```
- ✅ 收到回复 "OK"
- ❌ 超时或报错

---

### Step 5：记录结果

**必须按以下格式记录，不允许省略任何字段：**

```
工具状态检查（YYYY-MM-DD HH:MM）：
- Chrome CDP 18800: ✅ Chrome/146.x.x.x
- Doubao: ✅ (Xs) / ❌ 超时 / ❌ 错误信息
- Kimi: ✅ (Xs) / ❌ 超时 / ❌ 错误信息
- GLM: ✅ (Xs) / ❌ 超时 / ❌ 错误信息
- Qwen: ✅ (Xs) / ❌ 超时 / ❌ 错误信息
- DeepSeek: ✅ (Xs) / ❌ 超时 / ❌ 错误信息
- minimax search: ✅ (Xs) / ❌ 错误信息
- tavily: ✅ (Xs) / ❌ 错误信息
- subagent: ✅ (Xs) / ❌ 超时 / ❌ 错误信息
```

---

## 发现工具不可用时的处理

**停下来，问用户：**
> "XXX 工具不可用（原因），是要先修复还是直接用能用的工具继续？"

**绝对禁止：**
- ❌ 发现工具不可用但不告诉用户，偷偷用不完整的工具继续调研
- ❌ 跳过不可用的工具，假装所有工具都正常
- ❌ 只修一个问题就开始调研，不完整验证所有工具

---

## 完整参考：webauth 工具调用方式

| 平台 | 函数名 | 最小调用参数 |
|------|--------|------------|
| 豆包 | `doubao_doubao_chat` | `message="OK", thinking=true` |
| Kimi | `kimi_kimi_chat` | `message="OK", thinking=true` |
| 智谱 | `glm_glm_chat` | `message="OK", thinking=true` |
| 千问 | `qwen_qwen_chat` | `message="OK", thinking=true` |
| DeepSeek | `deepseek_deepseek_chat` | `message="OK", thinking=true, search=false` |

---

### mdview.py 打开 SOP 文件的正确流程

**当前 mdview 版本**（2026-03-24 多次修复后）：`~/.openclaw/workspace/tools/mdview.py`

**正确操作流程：**
1. 执行 `python3 ~/.openclaw/workspace/tools/mdview.py <文件路径>`
2. mdview 会自动检测是否已有服务器在运行：
   - **有** → 直接打开 URL（HTML 文件已更新），**不会打开新标签页**，不会启动新进程
   - **没有** → 启动新服务器，打开浏览器
3. 连续执行多次 mdview 不会产生多个标签页（已修复）

**原理（防重复标签页 + 防僵尸进程）：**
- 启动前用 `ps aux | grep mdview.py` 检查是否有已有进程
- 有 → 复用已有服务器，不启动新的，直接 return 退出
- 没有 → 启动服务器，`threading.Event` 确认启动成功，`urllib` 验证服务响应
- 服务器未响应 → `os._exit(1)` 强制退出整个进程（不是 `sys.exit` 只退线程）

**如果 mdview 报错或卡住：**
1. `ps aux | grep mdview.py | grep -v grep` 查看是否有僵尸进程
2. 有 → `kill <PID>` 杀掉，再重新执行 mdview
3. 不要连续执行多次，会打开多个标签页

**教训（2026-03-24 两次错误）：**
- **错误1**：一看到"端口占用"报错就连续重试 → 打开了 3 个重复标签页
  - 教训：报错 ≠ 失败，先验证（`curl`）再决定是否重试
- **错误2**：修复时反复尝试 5-6 种方案才找到最简解（ps aux 检测进程）
  - 教训：先想最简方案再动手，最终有效的往往最简单
- **错误3**：daemon 线程中 `sys.exit(1)` 只退线程不退进程 → 僵尸进程
  - 教训：daemon 线程的异常主线程感知不到，必须用 `os._exit` 强杀

---

## 为什么这是正确的检查方式

- **Chrome CDP 检查** → 验证 Chrome 调试端口可用（5个工具的基础）
- **直接调用每个 webauth 工具** → 同时验证：MCP Server 运行正常 + 登录凭证有效 + 网络连通
- **搜索工具测试** → 验证联网搜索可用
- **subagent 测试** → 验证子 agent 调度正常

三个层次缺一不可。

---

## 本 SOP 编写背景

- **日期：** 2026-03-24
- **原因：** MiniMax 在多次 deep-research 任务中用 Playwright 打开页面代替直接调用工具，导致工具实际不可用时没有发现
- **教训：** "页面能加载" ≠ "工具能用"，必须实际调用工具本身验证
