#!/usr/bin/env python3
"""
Skill Evolution - 从任务日志中自动提取高频任务并推荐注册为 Skill
"""
import json
import os
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

# 配置
TASKS_FILE = os.path.expanduser("~/.semantic_cache/tasks/tasks_index.jsonl")
THRESHOLD = 3  # 达到此阈值则推荐注册 Skill
OUTPUT_DIR = os.path.expanduser("~/.openclaw/workspace/skills")
REPORT_FILE = os.path.expanduser("~/.openclaw/workspace/memory/2026-04-02-A23-Skill-Evolution-Report.md")

def slugify(name: str) -> str:
    """将任务名转换为安全的目录名"""
    # 移除特殊字符，转小写，空格变横线
    name = re.sub(r'[^\w\s-]', '', name)
    name = re.sub(r'[\s/]+', '-', name.lower())
    return name.strip('-')

def load_tasks() -> list:
    """读取 tasks_index.jsonl"""
    tasks = []
    if not os.path.exists(TASKS_FILE):
        print(f"⚠️ 文件不存在: {TASKS_FILE}")
        return tasks
    
    with open(TASKS_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    tasks.append(json.loads(line))
                except json.JSONDecodeError as e:
                    print(f"⚠️ JSON 解析错误: {e}")
    return tasks

def analyze_tasks(tasks: list) -> dict:
    """统计 task_name 频率"""
    task_names = [t.get('task_name', 'unknown') for t in tasks]
    freq = Counter(task_names)
    
    results = []
    for name, count in freq.most_common():
        # 根据出现次数评级
        if count >= THRESHOLD:
            level = "🔥 强烈推荐"
        elif count >= 2:
            level = "⚠️ 观察中"
        else:
            level = "📊 数据不足"
        
        results.append({
            'task_name': name,
            'count': count,
            'level': level,
            'recommended': count >= THRESHOLD
        })
    
    return {
        'total_tasks': len(tasks),
        'unique_tasks': len(freq),
        'threshold': THRESHOLD,
        'results': results
    }

def generate_skill_skeleton(task_name: str, count: int) -> dict:
    """生成 Skill 骨架"""
    slug = slugify(task_name)
    skill_dir = os.path.join(OUTPUT_DIR, slug)
    
    return {
        'task_name': task_name,
        'slug': slug,
        'dir': skill_dir,
        'exists': os.path.exists(skill_dir),
        'count': count
    }

def create_skill_files(skeleton: dict) -> bool:
    """创建 Skill 文件结构"""
    if skeleton['exists']:
        return False
    
    os.makedirs(skeleton['dir'], exist_ok=True)
    task_name = skeleton['task_name']
    slug = skeleton['slug']
    
    # SKILL.md
    skill_md = f"""# {task_name}

## 描述
自动提取的 Skill - 基于任务 "{task_name}" 执行 {skeleton['count']} 次。

## 触发条件
当用户请求类似以下内容时自动触发：
- {task_name}
- 相关变体

## 使用方法
```bash
# 使用方式
```

## 注意事项
- 由 skill_evolution.py 自动生成
- 需要根据实际使用场景完善
"""
    
    # README.md
    readme_md = f"""# {task_name}

- **来源**: 自动从 tasks_index.jsonl 提取
- **出现次数**: {skeleton['count']}
- **目录**: `{slug}/`

## 使用说明
见 SKILL.md
"""
    
    # Python 脚本（占位符）
    py_file = f"""#!/usr/bin/env python3
\"\"\"
{task_name}
自动生成的 Skill 脚本
\"\"\"

def execute(params: dict = None):
    \"\"\"执行 Skill\"\"\"
    print("执行 {task_name}")
    # TODO: 实现具体逻辑
    return {{"status": "ok"}}

if __name__ == "__main__":
    execute()
"""
    
    # 写入文件
    with open(os.path.join(skeleton['dir'], 'SKILL.md'), 'w', encoding='utf-8') as f:
        f.write(skill_md)
    with open(os.path.join(skeleton['dir'], 'README.md'), 'w', encoding='utf-8') as f:
        f.write(readme_md)
    with open(os.path.join(skeleton['dir'], f'{slug}.py'), 'w', encoding='utf-8') as f:
        f.write(py_file)
    
    return True

def generate_report(analysis: dict, skeletons: list) -> str:
    """生成推荐报告"""
    lines = [
        "# Skill Evolution Report",
        f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**任务总数**: {analysis['total_tasks']}",
        f"**唯一任务数**: {analysis['unique_tasks']}",
        f"**阈值**: >= {analysis['threshold']} 次",
        "",
        "---",
        "",
        "## 任务统计",
        "",
        "| Task Name | 出现次数 | 推荐级别 |",
        "|-----------|----------|----------|",
    ]
    
    for r in analysis['results']:
        lines.append(f"| {r['task_name']} | {r['count']} | {r['level']} |")
    
    lines.extend([
        "",
        "---",
        "",
        "## 推荐详情",
        "",
    ])
    
    # 推荐的 Skill
    recommended = [s for s in skeletons if s['count'] >= THRESHOLD]
    if recommended:
        lines.append("### 🔥 强烈推荐注册")
        for s in recommended:
            lines.append(f"""
#### {s['task_name']}
- **出现次数**: {s['count']}
- **目录**: `{s['slug']}/`
- **状态**: {'已存在' if s['exists'] else '可创建'}
- **建议**: 创建完整 Skill 实现
""")
    else:
        lines.append("### ⚠️ 无达到阈值的任务")
        lines.append("当前没有任务达到阈值，建议继续积累数据。")
    
    # 观察中的任务
    observing = [s for s in skeletons if 2 <= s['count'] < THRESHOLD]
    if observing:
        lines.append("\n### ⚠️ 观察中（接近阈值）")
        for s in observing:
            remaining = THRESHOLD - s['count']
            lines.append(f"- **{s['task_name']}**: 还差 {remaining} 次达到阈值")
    
    lines.extend([
        "",
        "---",
        "",
        "## 推理过程",
        "",
        f"- 统计 {analysis['total_tasks']} 条任务记录",
        f"- 识别 {analysis['unique_tasks']} 个唯一任务",
        f"- 阈值设定: {THRESHOLD} 次",
        "- 判定标准: 同一任务执行 >= 3 次说明是高频需求，值得提取为 Skill",
        "- 当前样本量较小，建议持续观察",
    ])
    
    return "\n".join(lines)

def main():
    print("🔍 扫描任务日志...")
    tasks = load_tasks()
    
    if not tasks:
        print("❌ 没有找到任务记录")
        return
    
    print(f"📊 共加载 {len(tasks)} 条记录")
    
    # 分析
    analysis = analyze_tasks(tasks)
    
    # 生成骨架
    skeletons = []
    for r in analysis['results']:
        skeleton = generate_skill_skeleton(r['task_name'], r['count'])
        skeletons.append(skeleton)
        
        # 自动创建达到阈值的 Skill（可选）
        if r['recommended'] and not skeleton['exists']:
            print(f"  ➜ 自动创建 Skill: {r['task_name']}")
            create_skill_files(skeleton)
    
    # 生成报告
    report = generate_report(analysis, skeletons)
    
    # 确保目录存在
    os.makedirs(os.path.dirname(REPORT_FILE), exist_ok=True)
    
    # 保存报告
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n✅ 报告已生成: {REPORT_FILE}")
    print(f"\n📈 统计摘要:")
    print(f"   总记录: {analysis['total_tasks']}")
    print(f"   唯一任务: {analysis['unique_tasks']}")
    print(f"   达到阈值: {sum(1 for r in analysis['results'] if r['recommended'])}")
    print(f"   观察中: {sum(1 for r in analysis['results'] if 2 <= r['count'] < THRESHOLD)}")

if __name__ == "__main__":
    main()