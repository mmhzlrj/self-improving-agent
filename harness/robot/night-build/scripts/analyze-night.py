#!/usr/bin/env python3
"""
Night Build 晨间分析脚本
每天早上由 GLM 调用，对比 A/B 组结果与 ground truth
"""

import json
import os
import sys
from datetime import datetime

BASE = os.path.expanduser("~/.openclaw/workspace/harness/robot/night-build")
REFERENCE = os.path.join(BASE, "reference/ground-truth-headings.json")

def load_ground_truth():
    with open(REFERENCE) as f:
        return json.load(f)

def load_result(date_dir, task_id):
    path = os.path.join(BASE, "output", date_dir, task_id, "result.json")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)

def extract_heading_set(result):
    """从 result 中提取 (line, level, heading) 集合"""
    headings = set()
    for h in result.get("headings", []):
        headings.add((h.get("line", 0), h.get("level", 0), h.get("heading", "")))
    return headings

def compare_sets(gt_set, result_set):
    """对比两个标题集合"""
    # 精确匹配：行号+标题都一致
    exact_match = gt_set & result_set
    # 行号对但标题不对
    gt_lines = {(line, level) for line, level, _ in gt_set}
    result_lines = {(line, level) for line, level, _ in result_set}
    line_match = gt_lines & result_lines
    
    missed = gt_set - result_set  # ground truth 有但结果没有
    extra = result_set - gt_set  # 结果有但 ground truth 没有
    
    return {
        "total_gt": len(gt_set),
        "total_result": len(result_set),
        "exact_match": len(exact_match),
        "line_match": len(line_match),
        "accuracy": len(exact_match) / len(gt_set) if gt_set else 0,
        "coverage": len(line_match) / len(gt_set) if gt_set else 0,
        "missed_count": len(missed),
        "extra_count": len(extra),
        "missed": sorted(missed)[:10],  # 最多展示 10 个
        "extra": sorted(extra)[:10],
    }

def analyze_task(date_dir, task_id, gt_set):
    result = load_result(date_dir, task_id)
    if result is None:
        return {"task_id": task_id, "status": "not_found"}
    if not result.get("headings"):
        return {"task_id": task_id, "status": "empty_result", "raw": result}
    
    result_set = extract_heading_set(result)
    comparison = compare_sets(gt_set, result_set)
    
    return {
        "task_id": task_id,
        "group": result.get("group", "unknown"),
        "status": "success",
        "total_headings_found": result.get("total_headings", len(result.get("headings", []))),
        **comparison
    }

def generate_report(date_dir):
    gt = load_ground_truth()
    gt_set = {(h["line"], h["level"], h["heading"]) for h in gt}
    
    # 扫描所有任务结果
    results = {}
    for task_id in sorted(os.listdir(os.path.join(BASE, "output", date_dir))):
        task_path = os.path.join(BASE, "output", date_dir, task_id)
        if os.path.isdir(task_path) and task_id != "preliminary-comparison":
            results[task_id] = analyze_task(date_dir, task_id, gt_set)
    
    # 分组统计
    a_results = {k: v for k, v in results.items() if v.get("group") == "A"}
    b_results = {k: v for k, v in results.items() if v.get("group") == "B"}
    
    # A 组统计（需要合并所有 A 组结果再对比）
    a_all_headings = set()
    a_total_tasks = 0
    a_success_tasks = 0
    for k, v in a_results.items():
        a_total_tasks += 1
        if v.get("status") == "success":
            a_success_tasks += 1
            r = load_result(date_dir, k)
            if r:
                a_all_headings |= extract_heading_set(r)
    
    a_comparison = compare_sets(gt_set, a_all_headings)
    
    # B 组每个任务单独统计
    b_comparisons = {}
    for k, v in b_results.items():
        if v.get("status") == "success":
            r = load_result(date_dir, k)
            if r:
                b_comparisons[k] = compare_sets(gt_set, extract_heading_set(r))
    
    report = {
        "date": date_dir,
        "generated_at": datetime.now().isoformat(),
        "ground_truth_total": len(gt),
        "group_a": {
            "total_tasks": a_total_tasks,
            "success_tasks": a_success_tasks,
            **a_comparison
        },
        "group_b": b_comparisons,
        "individual_results": results
    }
    
    return report

if __name__ == "__main__":
    import glob
    
    # 找最新的日期目录
    output_dir = os.path.join(BASE, "output")
    dirs = sorted(glob.glob(os.path.join(output_dir, "20*")))
    if not dirs:
        print("No output directories found")
        sys.exit(1)
    
    latest_dir = os.path.basename(dirs[-1])
    report = generate_report(latest_dir)
    
    # 输出 JSON
    report_path = os.path.join(BASE, "output", latest_dir, "analysis-report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    # 输出人类可读摘要
    print(f"# Night Build Analysis: {latest_dir}")
    print(f"Ground Truth: {report['ground_truth_total']} headings")
    print()
    
    a = report["group_a"]
    print(f"## A Group (Atomic Tasks)")
    print(f"Tasks: {a['success_tasks']}/{a['total_tasks']} completed")
    print(f"Found: {a['total_result']} headings (GT: {a['total_gt']})")
    print(f"Accuracy: {a['accuracy']:.1%} | Coverage: {a['coverage']:.1%}")
    print(f"Missed: {a['missed_count']} | Extra: {a['extra_count']}")
    print()
    
    for task_id, comp in report["group_b"].items():
        print(f"## {task_id}")
        print(f"Found: {comp['total_result']} headings")
        print(f"Accuracy: {comp['accuracy']:.1%} | Coverage: {comp['coverage']:.1%}")
        print(f"Missed: {comp['missed_count']} | Extra: {comp['extra_count']}")
        print()
    
    print(f"\nFull report: {report_path}")
