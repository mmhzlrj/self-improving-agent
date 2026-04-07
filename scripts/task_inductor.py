"""
TaskInductor: 从 Session 历史中提炼结构化任务记录
使用规则+关键词提取（当 LLM API 不可用时）

依赖：
- task_broadcast.py: 任务结果广播模块
"""
import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# 导入 TaskBroadcast
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))
try:
    from task_broadcast import publish_task, subscribe_tasks, check_task_exists
    TASK_BROADCAST_AVAILABLE = True
except ImportError:
    TASK_BROADCAST_AVAILABLE = False
    print("[TaskInductor] Warning: task_broadcast.py not available, skipping broadcast")

SESSIONS_DIR = Path.home() / ".openclaw/agents/main/sessions"
TASKS_DIR = Path.home() / ".semantic_cache/tasks"
TASKS_INDEX = TASKS_DIR / "tasks_index.jsonl"
DAILY_DIR = TASKS_DIR / "daily"

# LLM Prompt 模板（用于调试和后续 API 可用时）
LLM_PROMPT_TEMPLATE = """你是 0-1 项目的任务归纳助手。以下是一个 session 的对话记录：

{conversation}

请提炼为结构化任务记录，输出 JSON 格式：
{{
  "task_id": "session_xxx",
  "task_name": "简短任务名称",
  "outcome": "最终结果/产出",
  "decisions": ["决策点1", "决策点2"],
  "open_issues": ["未解决的问题1"],
  "key_insights": ["关键洞察1"],
  "related_task_ids": ["相关任务ID（如果有）"],
  "confidence": "high/medium/low"
}}

注意：
- task_name 要具体，不要泛泛
- 只输出 JSON，不要解释
- 如果对话内容太少（<3轮），confidence 设为 low
- conversation 中的用户名是 lr（用户），助手名是 AI
"""

# 任务类型关键词映射
TASK_KEYWORDS = {
    "代码开发": ["代码", "写", "实现", "开发", "function", "def ", "class ", "import "],
    "配置修复": ["修复", "错误", "bug", "配置", "setting", "config", "error", "问题"],
    "调研学习": ["调研", "研究", "学习", "了解", "调查", "search", "查找"],
    "文件操作": ["文件", "读取", "写入", "创建", "删除", "移动", "file", "write", "read"],
    "系统操作": ["安装", "部署", "启动", "停止", "重启", "install", "deploy", "start", "stop"],
    "浏览器操作": ["浏览器", "网页", "点击", "输入", "browser", "web", "click", "type"],
    "任务规划": ["计划", "方案", "规划", "步骤", "plan", "steps", "strategy"],
    "知识记录": ["记录", "笔记", "总结", "文档", "note", "document", "summary"],
}

def get_today_sessions():
    """获取今天的 session 文件"""
    today = datetime.now(timezone(timedelta(hours=8))).date()
    sessions = []
    # 注意：session 文件名是 UUID 格式，不是 session-*.jsonl
    for f in SESSIONS_DIR.glob("*.jsonl"):
        # 排除非 session 文件（如 channel-messages, feishu 等）
        if any(x in f.name for x in ['channel-messages', 'feishu-', 'feishu_']):
            continue
        try:
            mtime = datetime.fromtimestamp(f.stat().st_mtime, tz=timezone(timedelta(hours=8))).date()
            if mtime == today:
                sessions.append(f)
        except Exception:
            pass
    return sessions

def extract_conversation(session_path, max_turns=30):
    """从 session JSONL 中提取对话文本"""
    messages = []
    try:
        with open(session_path, 'r') as f:
            for line in f:
                try:
                    msg = json.loads(line)
                    # 提取 message 内容
                    if msg.get('type') == 'message':
                        content = msg.get('message', {}).get('content', [])
                        if isinstance(content, list):
                            text_parts = []
                            for c in content:
                                if isinstance(c, dict):
                                    if c.get('type') == 'text':
                                        text_parts.append(c.get('text', ''))
                                    elif c.get('type') == 'thinking':
                                        text_parts.append(f"[思考: {c.get('thinking', '')[:100]}...]")
                            content = ' '.join(text_parts)
                        elif isinstance(content, str):
                            pass
                        else:
                            content = ''
                        
                        if content:
                            role = msg.get('message', {}).get('role', '?')
                            messages.append(f"{role}: {content[:600]}")
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        return None
    return '\n'.join(messages[-max_turns*2:])

def extract_task_by_rules(conversation_text):
    """使用规则+关键词提取任务信息"""
    if not conversation_text or len(conversation_text) < 100:
        return None
    
    # 提取 session ID
    task_id = "session_unknown"
    
    # 检测任务类型
    task_type = "其他"
    max_matches = 0
    for ttype, keywords in TASK_KEYWORDS.items():
        matches = sum(1 for kw in keywords if kw.lower() in conversation_text.lower())
        if matches > max_matches:
            max_matches = matches
            task_type = ttype
    
    # 提取关键信息
    lines = conversation_text.split('\n')
    user_lines = [l for l in lines if l.startswith('user:')][:5]
    assistant_lines = [l for l in lines if l.startswith('assistant:')][:5]
    
    # 从用户消息中提取任务关键词
    task_keywords = []
    for line in user_lines:
        # 提取命令/请求类型的短语
        words = re.findall(r'[\u4e00-\u9fa5]{2,6}', line)
        task_keywords.extend(words[:5])
    
    # 生成任务名称
    if task_keywords:
        task_name = f"{task_type} - {'/'.join(task_keywords[:2])}"
    else:
        task_name = f"{task_type}任务"
    
    # 提取结果和决策点
    outcomes = []
    decisions = []
    open_issues = []
    insights = []
    
    # 关键词模式匹配
    outcome_patterns = [r'完成[了是]', r'解决[了是]', r'成功', r'结果[:：]', r'输出[:：]']
    decision_patterns = [r'决定', r'选择', r'采用', r'改用', r'使用', r'配置']
    issue_patterns = r'未完成|未解决|待处理|问题|不确定'
    insight_patterns = r'发现|注意|关键|重要|经验'
    
    for line in conversation_text.split('\n'):
        for pattern in outcome_patterns:
            if re.search(pattern, line):
                match = re.search(r'[:：](.+)$', line)
                if match:
                    outcomes.append(match.group(1).strip()[:50])
        for pattern in decision_patterns:
            if re.search(pattern, line):
                match = re.search(r'[:：](.+)$', line)
                if match:
                    decisions.append(match.group(1).strip()[:50])
        if re.search(issue_patterns, line):
            match = re.search(r'[:：](.+)$', line)
            if match:
                open_issues.append(match.group(1).strip()[:50])
        if re.search(insight_patterns, line):
            match = re.search(r'[:：](.+)$', line)
            if match:
                insights.append(match.group(1).strip()[:50])
    
    # 去重
    outcomes = list(dict.fromkeys(outcomes))[:3]
    decisions = list(dict.fromkeys(decisions))[:3]
    open_issues = list(dict.fromkeys(open_issues))[:2]
    insights = list(dict.fromkeys(insights))[:3]
    
    # 确定置信度
    if len(user_lines) >= 3 and (outcomes or decisions):
        confidence = "medium"
    elif len(user_lines) < 2:
        confidence = "low"
    else:
        confidence = "low"
    
    return {
        "task_id": task_id,
        "task_name": task_name,
        "outcome": outcomes[0] if outcomes else "处理中",
        "decisions": decisions,
        "open_issues": open_issues,
        "key_insights": insights,
        "related_task_ids": [],
        "confidence": confidence,
        "timestamp": datetime.now(timezone(timedelta(hours=8))).isoformat()
    }

def call_llm(conversation_text):
    """
    调用 LLM 提炼任务
    当前使用规则提取（API 不可用时的备选方案）
    """
    # TODO: 当 LLM API 可用时，替换为真正的 API 调用
    # 方案 1: 使用 MiniMax API (需要有效的 API key)
    # 方案 2: 使用 OpenClaw Gateway API
    # 方案 3: 使用豆包 Browser Relay
    
    # 使用规则提取作为备选
    return extract_task_by_rules(conversation_text)

def main():
    # 确保目录存在
    TASKS_DIR.mkdir(parents=True, exist_ok=True)
    DAILY_DIR.mkdir(parents=True, exist_ok=True)
    
    print(f"[TaskInductor] 开始扫描 sessions...")
    
    # Step 1: 订阅已存在的任务（避免重复处理）
    existing_tasks = []
    if TASK_BROADCAST_AVAILABLE:
        try:
            existing_tasks = subscribe_tasks(since_days=7)
            existing_task_ids = set(t["task_id"] for t in existing_tasks)
            print(f"[TaskInductor] 已有 {len(existing_tasks)} 个已完成任务")
        except Exception as e:
            print(f"[TaskInductor] Warning: Failed to subscribe tasks: {e}")
            existing_task_ids = set()
    else:
        existing_task_ids = set()
    
    sessions = get_today_sessions()
    print(f"[TaskInductor] 找到 {len(sessions)} 个今天的 sessions")
    
    results = []
    for session_path in sessions:
        # 跳过已存在的任务
        if session_path.stem in existing_task_ids:
            print(f"[TaskInductor] 跳过已存在任务: {session_path.name}")
            continue
            
        print(f"[TaskInductor] 处理: {session_path.name}")
        conv = extract_conversation(session_path)
        if not conv or len(conv) < 50:
            print(f"  跳过（内容太少）")
            continue
        
        task = call_llm(conv)
        if task:
            # 更新 task_id 为实际 session ID
            task['task_id'] = session_path.stem
            results.append(task)
            # 追加到 index
            with open(TASKS_INDEX, 'a') as f:
                f.write(json.dumps(task, ensure_ascii=False) + '\n')
            print(f"  成功: {task.get('task_name', 'unknown')}")
            
            # Step 2: 广播任务结果
            if TASK_BROADCAST_AVAILABLE:
                try:
                    # 判断任务状态（基于 confidence 和 outcome）
                    status = "completed" if task.get("confidence") in ["high", "medium"] else "in_progress"
                    publish_task(
                        task_id=task['task_id'],
                        status=status,
                        outcome=task.get("outcome", ""),
                        details={
                            "task_name": task.get("task_name", ""),
                            "confidence": task.get("confidence", ""),
                            "decisions": task.get("decisions", []),
                            "key_insights": task.get("key_insights", [])
                        }
                    )
                except Exception as e:
                    print(f"[TaskInductor] Warning: Failed to broadcast: {e}")
        else:
            print(f"  跳过（无法提取任务）")
    
    # 生成每日摘要
    today_str = datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d')
    summary_path = DAILY_DIR / f"{today_str}.md"
    with open(summary_path, 'w') as f:
        f.write(f"# 每日任务归纳摘要 - {today_str}\n\n")
        if not results:
            f.write("*今日无有效任务记录*\n")
        for t in results:
            f.write(f"## {t.get('task_name', 'unknown')}\n\n")
            f.write(f"- **任务ID**: `{t.get('task_id', 'unknown')}`\n")
            f.write(f"- **结果**: {t.get('outcome', '-')}\n")
            f.write(f"- **置信度**: {t.get('confidence', '-')}\n")
            if t.get('decisions'):
                f.write(f"- **决策**: {', '.join(t.get('decisions', []))}\n")
            if t.get('key_insights'):
                f.write(f"- **洞察**: {', '.join(t.get('key_insights', []))}\n")
            if t.get('open_issues'):
                f.write(f"- **待办**: {', '.join(t.get('open_issues', []))}\n")
            f.write("\n")
    
    print(f"\n[TaskInductor] 完成！")
    print(f"[TaskInductor] 处理了 {len(results)} 个 tasks")
    print(f"[TaskInductor] 索引: {TASKS_INDEX}")
    print(f"[TaskInductor] 摘要: {summary_path}")
    
    return len(results)

if __name__ == "__main__":
    main()