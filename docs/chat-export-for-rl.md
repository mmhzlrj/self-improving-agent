# OpenClaw 聊天记录导出给 RL 训练

## 一、OpenClaw 会话数据存储位置和格式

### 1.1 存储路径

OpenClaw 会话数据存在两个位置：

| 路径 | 内容 |
|------|------|
| `~/.openclaw/agents/main/sessions/` | 所有会话的 JSONL 原始记录 |
| `~/.openclaw/agents/main/sessions/sessions.json` | 会话元数据索引 |
| `~/.openclaw/memory/main.sqlite` | 长期记忆向量数据库（embedding chunks） |
| `~/.openclaw/workspace/openclaw-zero-token/.openclaw-zero-state/agents/main/sessions/` | zero-token 版存储（格式相同但实际文件不落地） |

**当前用户实际数据量：**
- 229 个 session 文件，总计约 17.4 MB
- 位置：`~/.openclaw/agents/main/sessions/`

### 1.2 存储格式详解

每个会话是一个 **JSONL** 文件（每行一个 JSON 对象），文件名为 `{sessionId}.jsonl`。

#### 行类型（line type）

| `type` 值 | 说明 |
|-----------|------|
| `session` | 会话初始化头信息（id、timestamp、cwd） |
| `model_change` | 模型切换记录（provider、modelId） |
| `thinking_level_change` | thinking 级别变更 |
| `message` | 消息主体（最常见） |
| `custom` | 自定义消息 |
| `custom_message` | 自定义消息（变体） |

#### message 类型详解

一条 `message` 类型的行结构如下：

```json
{
  "type": "message",
  "id": "a35ed1fa",
  "parentId": "dabee47e",       // 父消息 ID，构成对话树
  "timestamp": "2026-03-27T23:39:16.166Z",
  "message": {
    "role": "assistant",        // user | assistant | system | toolResult
    "content": [
      { "type": "thinking", "thinking": "...", "thinkingSignature": "..." },
      { "type": "toolCall", "id": "...", "name": "exec", "arguments": {...} },
      { "type": "text", "text": "回复文本" }
    ],
    "api": "anthropic-messages",
    "provider": "minimax",
    "model": "MiniMax-M2.7",
    "usage": { "input": 48, "output": 212, "cacheRead": 16708, ... },
    "stopReason": "toolUse",    // end_turn | stop | toolUse | ...
    "timestamp": 1774654746605,
    "responseId": "0616481a..."
  }
}
```

#### toolResult 消息

```json
{
  "type": "message",
  "id": "83d2785d",
  "parentId": "a35ed1fa",
  "message": {
    "role": "toolResult",
    "toolCallId": "call_function_6lxidimdpjm6_1",
    "toolName": "exec",
    "content": [{ "type": "text", "text": "命令输出..." }],
    "isError": false,
    "timestamp": 1774654756650
  }
}
```

#### user 消息

```json
{
  "type": "message",
  "id": "dabee47e",
  "message": {
    "role": "user",
    "content": [{ "type": "text", "text": "用户输入..." }]
  }
}
```

### 1.3 重要字段说明

- **`parentId`**：构成对话树的核心字段。同一个 conversation 的消息通过 parentId 串联成链
- **`sessionId`**：在 `sessions.json` 中可通过 `sessionId` 关联到具体文件
- **`X-Session-Id` header**：RL 训练 headers 插件注入，每个 LLM API 请求都会带上

---

## 二、导出聊天记录的方法

### 2.1 直接读取 JSONL 文件（推荐）

OpenClaw 没有提供专门的导出命令，但数据结构是标准 JSONL，直接读取即可：

```bash
# 查看所有会话文件
ls -la ~/.openclaw/agents/main/sessions/*.jsonl

# 查看会话索引
cat ~/.openclaw/agents/main/sessions/sessions.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
for k, v in data.items():
    print(f'{k} -> sessionId={v.get(\"sessionId\")}, updatedAt={v.get(\"updatedAt\")}')"

# 读取单个会话（按时间戳排序的对话流）
python3 -c "
import json
session_file = '~/.openclaw/agents/main/sessions/{sessionId}.jsonl'
with open(session_file) as f:
    for line in f:
        if not line.strip(): continue
        obj = json.loads(line)
        if obj.get('type') == 'message':
            msg = obj['message']
            role = msg.get('role')
            # 提取文本内容
            for c in msg.get('content', []):
                if c.get('type') == 'text':
                    print(f'[{role}] {c[\"text\"][:200]}')
                elif c.get('type') == 'toolCall':
                    print(f'[assistant toolCall] {c[\"name\"]}: {str(c.get(\"arguments\",{}))[:100]}')
"
```

### 2.2 导出为对话格式（对话树 → 线性序列）

由于 OpenClaw 用 parentId 构成对话树，导出训练数据时需要按时间排序线性化：

```python
#!/usr/bin/env python3
"""openclaw_session_to_conversation.py
将 OpenClaw JSONL 会话转换为线性对话列表，适合 RL 训练数据格式
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

def load_session(jsonl_path: str) -> list[dict]:
    """读取 session JSONL，返回按时间排序的消息列表"""
    messages = []
    with open(jsonl_path) as f:
        for line in f:
            if not line.strip(): continue
            obj = json.loads(line)
            if obj.get("type") == "message":
                messages.append(obj)
    # 按 timestamp 排序
    messages.sort(key=lambda m: m.get("timestamp", ""))
    return messages

def build_conversation_tree(messages: list[dict]) -> list[dict]:
    """将消息列表构建为带 parentId 引用的树结构"""
    by_id = {m["id"]: m for m in messages}
    
    # 找根消息（parentId 为 null 或不在 by_id 中）
    roots = [m for m in messages if m.get("parentId") is None or m["parentId"] not in by_id]
    
    def traverse(node):
        result = [node]
        children = [m for m in messages if m.get("parentId") == node["id"]]
        children.sort(key=lambda m: m.get("timestamp", ""))
        for child in children:
            result.extend(traverse(child))
        return result
    
    all_nodes = []
    for root in roots:
        all_nodes.extend(traverse(root))
    
    # 再次按 timestamp 全局排序
    all_nodes.sort(key=lambda m: m.get("timestamp", ""))
    return all_nodes

def extract_text_content(content: list) -> str:
    """从 content 数组提取纯文本"""
    texts = []
    for c in content:
        if c.get("type") == "text":
            texts.append(c["text"])
        elif c.get("type") == "toolCall":
            args_str = json.dumps(c.get("arguments", {}), ensure_ascii=False)
            texts.append(f"<tool_call name={c['name']} args={args_str}>")
        elif c.get("type") == "toolResult":
            for tc in c.get("content", []):
                if tc.get("type") == "text":
                    texts.append(f"<tool_result>{tc['text']}</tool_result>")
        elif c.get("type") == "thinking":
            # 可选择是否包含 thinking
            pass
    return "\n".join(texts)

def session_to_rl_format(jsonl_path: str, session_id: str) -> dict:
    """将单个会话转换为 RL 训练格式"""
    messages = load_session(jsonl_path)
    if not messages:
        return None
    
    conversation = build_conversation_tree(messages)
    
    turns = []
    for msg in conversation:
        role = msg.get("message", {}).get("role")
        if role not in ("user", "assistant"):
            continue
        content = msg.get("message", {}).get("content", [])
        text = extract_text_content(content)
        if text:
            turns.append({"role": role, "content": text})
    
    return {
        "session_id": session_id,
        "turns": turns,
        "model": messages[0].get("message", {}).get("model", "unknown"),
    }

# 使用示例
if __name__ == "__main__":
    sessions_dir = Path.home() / ".openclaw/agents/main/sessions"
    output = []
    for jsonl_file in sorted(sessions_dir.glob("*.jsonl")):
        session_id = jsonl_file.stem
        result = session_to_rl_format(str(jsonl_file), session_id)
        if result and len(result["turns"]) >= 2:
            output.append(result)
    
    # 输出为 JSONL
    with open("openclaw_conversations.jsonl", "w") as f:
        for item in output:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    
    print(f"导出 {len(output)} 个会话到 openclaw_conversations.jsonl")
```

### 2.3 按 X-Turn-Type 过滤（仅用户对话）

OpenClaw RL headers 插件将对话分类为：
- **`main`**：用户主动发起的对话轮次
- **`side`**：心跳、记忆刷新、cron 等后台任务

如果你只需要用户对话：

```python
# 读取 sessions.json 找到 sessionId
# 结合 rl-training-headers 的 session 记录进行过滤
# 参考 ~/.openclaw/openclaw.json 中 plugins.entries.rl-training-headers 配置
```

---

## 三、OpenClaw RL 数据格式

### 3.1 OpenClaw-RL 架构概述

**OpenClaw-RL** 不是直接"导出文件给 RL 训练"，而是一个**实时 RL 服务器**。核心架构：

```
OpenClaw (运行中) 
    ↓ HTTP 请求携带 X-Session-Id, X-Turn-Type headers
OpenClaw-RL Server (Python/Flask)
    ↓ 收集对话轨迹
slime RL Framework (Megatron + SGLang)
    ↓ GRPO 训练
模型权重更新
```

### 3.2 rl-training-headers 插件

这是 OpenClaw 官方的 RL 数据采集插件：

**安装位置**：OpenClaw 仓库 `extensions/rl-training-headers/`

**安装方式**：
```bash
# 复制到 extensions 目录
cp -r rl-training-headers ~/.openclaw/extensions/

# 启用插件
openclaw plugins enable rl-training-headers

# 重启 gateway
openclaw gateway restart
```

**注入的 HTTP headers**：

| Header | 值 | 说明 |
|--------|-----|------|
| `X-Session-Id` | UUID | 当前 agent session 标识 |
| `X-Turn-Type` | `main` 或 `side` | `main`=用户对话，`side`=后台任务 |

**配置（`~/.openclaw/openclaw.json`）**：
```json
{
  "plugins": {
    "entries": {
      "rl-training-headers": {
        "enabled": true,
        "config": {
          "sessionIdHeader": "X-Session-Id",
          "turnTypeHeader": "X-Turn-Type"
        }
      }
    }
  }
}
```

### 3.3 slime 训练数据格式

slime（THUDM 的 RL 训练框架）期望的训练数据格式：

```json
{
  "prompt": "用户问题...",
  "messages": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."},
    {"role": "tool", "name": "exec", "content": "命令输出..."}
  ],
  "reward": 1.0,
  "ground_truth": "期望的答案..."
}
```

**slime 支持的 RL 模式**：
1. **GRPO**：基于 binary feedback（后续状态推断奖励）
2. **On-policy Distillation**：从后续反馈中提取 hindsight hints

**关键配置项**：
```bash
# slime 启动参数
--custom-generate-function-path <your_generate_func>   # 自定义生成函数
--custom-rm-path <your_reward_func>                    # 自定义奖励模型
--advantage-estimator grpo
--eps-clip 0.2
```

### 3.4 OpenClaw → slime 数据转换流程

```
OpenClaw Session JSONL
    ↓ 解析 parentId 构建对话树
Conversation (user/assistant/toolResult 序列)
    ↓ 过滤 X-Turn-Type=main
User 对话数据
    ↓ 转换格式
slime 训练 JSONL (prompt + messages + reward)
    ↓
GRPO / On-policy Distillation 训练
    ↓
更新模型权重
```

---

## 四、需要注意的坑

### 坑 1：zero-token 版的会话文件不落地

⚠️ **严重问题**：如果你使用的是 `openclaw-zero-token` 版本（轻量版），session JSONL 文件**不会实际写入磁盘**，全部存在内存中。这意味着：
- 无法通过文件方式导出历史会话
- `sessions.json` 中的 `sessionFile` 字段指向不存在的文件

**解决方案**：切换到完整版 OpenClaw，或者在 zero-token 中添加会话持久化存储逻辑。

**检查方式**：
```bash
# zero-token 版 - JSONL 文件不存在
ls ~/.openclaw/workspace/openclaw-zero-token/.openclaw-zero-state/agents/main/sessions/*.jsonl 2>/dev/null
# 应该返回空

# 完整版 - JSONL 文件存在
ls ~/.openclaw/agents/main/sessions/*.jsonl | head -5
```

### 坑 2：parentId 构成的对话树不是线性序列

OpenClaw 的消息通过 `parentId` 形成树结构，而不是简单的线性列表。直接按文件行顺序读取会导致对话顺序混乱。

**必须**：先按 `timestamp` 全局排序，再用 `parentId` 构建树，最后做树的线性遍历。

### 坑 3：toolCall 的 arguments 是嵌套 JSON

`toolCall.arguments` 是一个对象而非字符串，导出时需要 `JSON.stringify()` 序列化。

```python
# 错误
text = f"{c['name']}: {c.get('arguments')}"

# 正确
args_str = json.dumps(c.get("arguments", {}), ensure_ascii=False)
text = f"<tool_call name={c['name']} args={args_str}>"
```

### 坑 4：sessions.json 过大导致性能问题

`sessions.json` 默认超过 10MB 时会**自动轮转**（`sessions.json.bak.{timestamp}`），保留 3 个备份。如果你的会话数据量大，注意清理旧备份。

### 坑 5：heartbeat/cron 会话污染训练数据

未过滤的会话包含大量 `X-Turn-Type=side` 的心跳和后台任务，**必须过滤掉**再用于 RL 训练，否则模型会学到无意义的重复模式。

### 坑 6：API credentials 和隐私

导出的对话数据**包含完整的 toolCall arguments**（含文件路径、API keys 等敏感信息），导出前需脱敏处理。

### 坑 7：sessions.json 中的 sessionFile 路径问题

旧版本存储的是**绝对路径**，新版本转换为相对路径。跨环境迁移时需要注意路径解析。

---

## 五、示例命令完整流程

### Step 1：确认会话数据位置

```bash
# 检查完整版会话目录
ls ~/.openclaw/agents/main/sessions/
# 应该看到 sessions.json 和多个 .jsonl 文件

# 检查 zero-token 版（不会有 .jsonl 文件）
ls ~/.openclaw/workspace/openclaw-zero-token/.openclaw-zero-state/agents/main/sessions/
```

### Step 2：安装 rl-training-headers 插件（实时采集模式）

```bash
# 如果用完整版 OpenClaw
cd ~/.openclaw/extensions
git clone https://github.com/Gen-Verse/OpenClaw-RL.git
cp -r OpenClaw-RL/extensions/rl-training-headers/ ./

# 配置启用
openclaw plugins enable rl-training-headers
openclaw gateway restart
```

### Step 3：运行数据导出脚本

```bash
# 保存为 ~/.openclaw/workspace/scripts/export_sessions.py
python3 ~/.openclaw/workspace/scripts/export_sessions.py

# 输出：openclaw_conversations.jsonl（每个会话一行）
```

### Step 4：转换为 slime 训练格式

```python
#!/usr/bin/env python3
"""conversations_to_slime.py
将导出的对话转换为 slime GRPO 训练格式
"""
import json

def to_slime_format(conv: dict) -> dict:
    """转换为 slime 期望的格式"""
    turns = conv["turns"]
    if not turns:
        return None
    
    # 找到 user 的第一条消息作为 prompt
    prompt = next((t["content"] for t in turns if t["role"] == "user"), "")
    
    # 构建 messages（跳过第一条 user，保留后续作为 history）
    messages = []
    for t in turns:
        if t["role"] == "user":
            messages.append({"role": "user", "content": t["content"]})
        elif t["role"] == "assistant":
            messages.append({"role": "assistant", "content": t["content"]})
    
    return {
        "prompt": prompt,
        "messages": messages,
        "session_id": conv["session_id"],
        # reward 需要自己实现奖励函数
    }

# 转换
with open("openclaw_conversations.jsonl") as f:
    lines = [json.loads(l) for l in f]

slime_data = [to_slime_format(c) for c in lines]
slime_data = [x for x in slime_data if x]

with open("slime_training_data.jsonl", "w") as f:
    for item in slime_data:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")

print(f"导出 {len(slime_data)} 条 slime 训练数据")
```

### Step 5：验证导出结果

```bash
# 统计
wc -l openclaw_conversations.jsonl
wc -l slime_training_data.jsonl

# 查看样本
head -1 openclaw_conversations.jsonl | python3 -m json.tool | head -50
```

---

## 六、相关资源链接

| 资源 | 链接 |
|------|------|
| OpenClaw-RL 仓库 | https://github.com/Gen-Verse/OpenClaw-RL |
| rl-training-headers 插件文档 | https://github.com/Gen-Verse/OpenClaw-RL/blob/main/extensions/rl-training-headers/README.md |
| slime RL 框架 | https://github.com/THUDM/slime |
| slime Search-R1 示例（多轮对话+tool calling） | https://github.com/THUDM/slime/blob/main/examples/search-r1/README.md |
| slime On-policy Distillation | https://github.com/THUDM/slime/blob/main/examples/on_policy_distillation/ |

---

## 七、快速参考

```
# 会话存储位置
~/.openclaw/agents/main/sessions/*.jsonl      ← 完整版
~/.openclaw/agents/main/sessions/sessions.json ← 索引

# 关键字段
parentId      ← 对话树结构
role          ← user/assistant/toolResult
X-Session-Id  ← RL header (session 标识)
X-Turn-Type   ← RL header (main=用户对话, side=后台)

# rl-training-headers 插件安装
cp -r extensions/rl-training-headers ~/.openclaw/extensions/
openclaw plugins enable rl-training-headers
openclaw gateway restart

# slime 期望格式
{prompt, messages, reward, ground_truth}
```
