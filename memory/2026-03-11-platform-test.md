# 各平台网页版测试结果 (更新)

## 2026-03-11 15:00+ 统一测试

### 测试方法
1. 导航到页面
2. `document.querySelector("textarea")` 找输入框
3. 设置 value + dispatchEvent('input')
4. 回车发送 或 遍历找发送按钮
5. 等待 20 秒
6. 获取回答

### 结果

| 平台 | 状态 | 输入框类型 | 发送方式 | 结果 |
|------|------|------------|----------|------|
| 豆包 | ✅ | textarea | 遍历找按钮 | **成功** |
| 千问 | ✅ | textarea | 回车键 | **成功** |
| 智谱 | ✅ | textarea | 回车键 | **成功** |
| Kimi | ✅ | div[contenteditable] | 回车键 | **成功** |
| DeepSeek | ⚠️ | textarea | 按钮 disabled | **失败** |

### DeepSeek 问题
- 发送按钮 e54 是 disabled 状态
- 回车键不触发发送
- 需要进一步研究如何启用
