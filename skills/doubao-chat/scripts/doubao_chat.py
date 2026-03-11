#!/usr/bin/env python3
"""
豆包网页版 AI 对话助手
通过 Browser Relay 控制豆包标签页进行联网搜索和图片识别
"""

import subprocess
import json
import time
import sys
import re


def call_browser_relay(action, targetId=None, **kwargs):
    """调用 Browser Relay API"""
    cmd = [
        "curl", "-s", "-X", "POST",
        "http://localhost:9222/json/act",
        "-H", "Content-Type: application/json"
    ]
    
    payload = {"kind": action, "targetId": targetId, **kwargs}
    cmd.extend(["-d", json.dumps(payload)])
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout


def type_and_send(text, targetId=None):
    """在输入框输入文本并发送"""
    # 先聚焦输入框
    call_browser_relay("click", targetId=targetId, ref="e403")
    time.sleep(0.3)
    
    # 输入文本
    call_browser_relay("type", targetId=targetId, ref="e403", text=text)
    time.sleep(0.3)
    
    # 按 Enter 发送
    call_browser_relay("press", targetId=targetId, key="Enter")
    time.sleep(0.3)


def get_page_content(targetId=None):
    """获取页面内容"""
    result = call_browser_relay("snapshot", targetId=targetId)
    try:
        data = json.loads(result)
        return data
    except:
        return {}


def wait_for_response(targetId=None, timeout=30):
    """等待豆包生成回答"""
    start = time.time()
    while time.time() - start < timeout:
        content = get_page_content(targetId)
        # 检查是否有回答生成（根据页面结构调整检测逻辑）
        if content and content.get("content"):
            # 可以添加更精确的检测逻辑
            time.sleep(2)  # 额外等待确保回答完整
            return True
        time.sleep(1)
    return False


def doubao_search(query, targetId=None):
    """
    使用豆包进行联网搜索/问答
    
    Args:
        query: 用户问题
        targetId: 浏览器标签页 ID（可选）
    
    Returns:
        str: 豆包的回答
    """
    print(f"🔍 豆包搜索: {query}")
    
    # 输入问题并发送
    type_and_send(query, targetId)
    
    # 等待回答
    print("⏳ 等待豆包回答...")
    if wait_for_response(targetId):
        # 获取回答内容
        content = get_page_content(targetId)
        # 提取回答文本（根据实际页面结构调整）
        answer = extract_answer(content)
        return answer
    else:
        return "等待回答超时"


def extract_answer(content):
    """从页面内容中提取回答"""
    # 这里需要根据实际页面结构调整
    # 可以通过分析页面结构来提取 AI 回复
    try:
        if isinstance(content, dict):
            # 尝试提取文本内容
            text = content.get("content", "") or content.get("text", "")
            return text
        return str(content)
    except Exception as e:
        return f"提取回答失败: {e}"


def doubao_analyze_image(image_path, targetId=None):
    """
    使用豆包分析图片（暂不推荐）
    
    Args:
        image_path: 图片路径
        targetId: 浏览器标签页 ID（可选）
    
    Returns:
        str: 豆包的分析结果
    """
    # 图片上传功能暂不实现
    return "图片上传功能暂不实现"


if __name__ == "__main__":
    # 测试用
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        result = doubao_search(query)
        print("\n📝 豆包回答:")
        print(result)
    else:
        print("用法: python doubao_chat.py <问题>")
