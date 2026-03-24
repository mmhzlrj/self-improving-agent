#!/usr/bin/env python3
"""读取 mdview 审批结果

优先级：
1. 通过 Playwright CDP 从 Chrome localStorage 实时读取
2. 读取 ~/Downloads/review-results-*.json（导出文件）
3. 指定文件路径

用法:
  python3 read-review-results.py                      # 自动检测
  python3 read-review-results.py /path/to/results.json  # 读取指定文件
"""

import json
import os
import sys
import glob

CDP_PORT = 9223
PAGE_URL = "http://127.0.0.1:18999/index.html"


def read_from_cdp():
    """通过 Chrome DevTools Protocol 读取 localStorage"""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return None

    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{CDP_PORT}")
            page = None
            for ctx in browser.contexts:
                for pg in ctx.pages:
                    if PAGE_URL in pg.url:
                        page = pg
                        break
                if page:
                    break

            if not page:
                browser.close()
                return None

            raw = page.evaluate("""() => {
                const key = 'mdview_review_' + document.title;
                return localStorage.getItem(key);
            }""")

            browser.close()

            if raw:
                return json.loads(raw)
    except Exception:
        pass
    return None


def read_from_downloads():
    """从 ~/Downloads 读取导出的 JSON"""
    pattern = os.path.expanduser("~/Downloads/review-results-*.json")
    files = sorted(glob.glob(pattern))
    if not files:
        return None
    with open(files[-1], "r", encoding="utf-8") as f:
        data = json.load(f)
    # 导出格式是列表，转换为字典
    if isinstance(data, list):
        return {item["id"]: item for item in data}
    return data


def read_from_file(filepath):
    """从指定文件读取"""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return {item["id"]: item for item in data}
    return data


def display(data):
    """显示审批结果"""
    if isinstance(data, dict):
        items = list(data.items())
    else:
        items = [(item.get("id", "?"), item) for item in data]

    approved = sum(1 for _, v in items if v.get("status") == "approved")
    rejected = sum(1 for _, v in items if v.get("status") == "rejected")
    pending = sum(1 for _, v in items if v.get("status") == "pending")
    total = len(items)

    print(f"\n📋 审批结果总览")
    print(f"   总计: {total} | ✅ 采纳: {approved} | ❌ 拒绝: {rejected} | ⏳ 待审: {pending}")
    print()

    for item_id, info in sorted(items, key=lambda x: str(x[0])):
        emoji = {"approved": "✅", "rejected": "❌", "pending": "⏳"}.get(info.get("status"), "❓")
        label = {"approved": "采纳", "rejected": "拒绝", "pending": "待审"}.get(info.get("status"), "未知")
        title = info.get("title", "")
        note = info.get("note", "").strip()
        time_str = info.get("time", "")[:19]

        line = f"{emoji} [{item_id}] {title} — {label}"
        print(line)
        if note:
            print(f"   📝 {note}")
        if time_str:
            print(f"   🕐 {time_str}")
        print()

    return total, approved, rejected, pending


def main():
    data = None
    source = ""

    if len(sys.argv) > 1:
        path = os.path.expanduser(sys.argv[1])
        if os.path.exists(path):
            data = read_from_file(path)
            source = f"文件: {path}"
        else:
            print(f"❌ 文件不存在: {path}")
            sys.exit(1)
    else:
        # 优先 CDP，然后 Downloads
        data = read_from_cdp()
        if data:
            source = "Chrome localStorage (CDP)"
        else:
            data = read_from_downloads()
            if data:
                source = "~/Downloads 导出文件"
            else:
                print("❌ 未找到审批结果")
                print("   尝试: python3 read-review-results.py /path/to/results.json")
                sys.exit(1)

    print(f"📥 来源: {source}")
    display(data)

    # 保存到 .review 目录
    out = os.path.expanduser("~/.openclaw/workspace/.review/review-results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"💾 结果已保存到: {out}")


if __name__ == "__main__":
    main()
