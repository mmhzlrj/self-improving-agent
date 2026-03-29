#!/usr/bin/env node
/**
 * 智库主脚本 - 并行向5个平台提问，汇总结果
 * 
 * 使用方式：
 *   node zhiku-ask.js "如何设计高可用的分布式系统？"
 * 
 * 输出：各平台回复的汇总分析
 */

import { chromium } from 'playwright-core';
import { createHash, randomUUID } from 'crypto';
import { readFileSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';
import { homedir } from 'os';

const __dirname = dirname(fileURLToPath(import.meta.url));
const CREDENTIALS_DIR = resolve(homedir(), '.openclaw/workspace/auth-credentials');
const CDP_PORT = 18800;

// ─────────────────────────────────────────────
// MCP Server 路径
// ─────────────────────────────────────────────
const DOUBAO_MCP = resolve(homedir(), '.openclaw/extensions/doubao-mcp-server/doubao-mcp-server.mjs');
const KIMI_MCP = resolve(homedir(), '.openclaw/extensions/kimi-mcp-server/kimi-mcp-server.mjs');
const GLM_MCP = resolve(homedir(), '.openclaw/extensions/glm-mcp-server/glm-mcp-server.mjs');
const QWEN_MCP = resolve(homedir(), '.openclaw/extensions/qwen-mcp-server/qwen-mcp-server.mjs');
const DEEPSEEK_MCP = resolve(homedir(), '.openclaw/extensions/deepseek-mcp-server/deepseek-mcp-server.mjs');

// ─────────────────────────────────────────────
// 工具函数：调用 MCP Server（stdio JSON-RPC）
// ─────────────────────────────────────────────
function mcpCall(scriptPath, toolName, args) {
  return new Promise(async (resolve, reject) => {
    const { spawn } = (await import('child_process')).default;
    const proc = spawn('node', [scriptPath], { stdio: ['pipe', 'pipe', 'pipe'] });
    let stdout = '';
    let stderr = '';

    proc.stdout.on('data', d => { stdout += d.toString(); });
    proc.stderr.on('data', d => { stderr += d.toString(); });

    // 初始化
    proc.stdin.write(JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'initialize', params: { protocolVersion: '2024-11-05', capabilities: { tools: {} }, serverInfo: { name: 'zhiku', version: '1.0.0' } } }) + '\n');
    // tools/list
    proc.stdin.write(JSON.stringify({ jsonrpc: '2.0', id: 2, method: 'tools/list', params: {} }) + '\n');
    // tools/call
    proc.stdin.write(JSON.stringify({ jsonrpc: '2.0', id: 3, method: 'tools/call', params: { name: toolName, arguments: args } }) + '\n');
    proc.stdin.end();

    setTimeout(() => {
      proc.kill();
      // 解析多行 JSON-RPC 响应，找 tools/call 的结果
      const lines = stdout.split('\n').filter(Boolean);
      for (const line of lines.reverse()) {
        try {
          const obj = JSON.parse(line);
          if (obj.result?.content?.[0]?.text) {
            const text = obj.result.content[0].text;
            resolve(obj.result.isError ? `❌ ${text}` : text);
            return;
          }
        } catch {}
      }
      resolve('[无响应] ' + stdout.slice(0, 200));
    }, 90000);

    proc.on('error', reject);
  });
}

// ─────────────────────────────────────────────
// 平台调用函数（每个平台独立）
// ─────────────────────────────────────────────

async function askDeepSeek(question) {
  try {
    return await mcpCall(DEEPSEEK_MCP, 'deepseek_chat', {
      message: question,
      thinking: true,
      search: true
    });
  } catch (e) {
    return `❌ DeepSeek 错误: ${e.message}`;
  }
}

async function askKimi(question) {
  try {
    return await mcpCall(KIMI_MCP, 'kimi_chat', { message: question });
  } catch (e) {
    return `❌ Kimi 错误: ${e.message}`;
  }
}

async function askDoubao(question) {
  try {
    return await mcpCall(DOUBAO_MCP, 'doubao_chat', { message: question });
  } catch (e) {
    return `❌ Doubao 错误: ${e.message}`;
  }
}

async function askGLM(question) {
  try {
    return await mcpCall(GLM_MCP, 'glm_chat', { message: question });
  } catch (e) {
    return `❌ GLM 错误: ${e.message}`;
  }
}

async function askQwen(question) {
  try {
    return await mcpCall(QWEN_MCP, 'qwen_chat', { message: question });
  } catch (e) {
    return `❌ Qwen 错误: ${e.message}`;
  }
}

// ─────────────────────────────────────────────
// 主函数
// ─────────────────────────────────────────────
async function main(question) {
  console.error('🔵 智库启动，问题:', question);

  // 并行向 5 个平台提问
  const [deepseek, kimi, doubao, glm, qwen] = await Promise.all([
    askDeepSeek(question).catch(e => `❌ DeepSeek: ${e.message}`),
    askKimi(question).catch(e => `❌ Kimi: ${e.message}`),
    askDoubao(question).catch(e => `❌ Doubao: ${e.message}`),
    askGLM(question).catch(e => `❌ GLM: ${e.message}`),
    askQwen(question).catch(e => `❌ Qwen: ${e.message}`),
  ]);

  // 输出汇总（stdout 输出 JSON 格式供主会话解析）
  const summary = formatSummary(question, { deepseek, kimi, doubao, glm, qwen });
  console.log(JSON.stringify({ success: true, summary, raw: { deepseek, kimi, doubao, glm, qwen } }));
}

// ─────────────────────────────────────────────
// 格式化汇总输出
// ─────────────────────────────────────────────
function formatSummary(question, results) {
  const { deepseek, kimi, doubao, glm, qwen } = results;

  const truncate = (s, len = 300) => {
    if (!s || s === '[无响应]') return '⚠️ 无响应';
    if (s.length <= len) return s;
    return s.slice(0, len) + '...（已截断）';
  };

  const lines = [];

  lines.push(`## 🧠 智库对比分析`);
  lines.push('');
  lines.push(`**问题：** ${question}`);
  lines.push('');
  lines.push(`---`);
  lines.push('');
  lines.push(`### 各平台回复`);
  lines.push('');

  lines.push(`**🔵 DeepSeek（深度思考+联网搜索）**`);
  lines.push(truncate(deepseek, 500));
  lines.push('');

  lines.push(`**🟣 Kimi（K2.5 思考模式，200万字上下文）**`);
  lines.push(truncate(kimi, 500));
  lines.push('');

  lines.push(`**🟠 Doubao（专家模式，研究级深度思考）**`);
  lines.push(truncate(doubao, 500));
  lines.push('');

  lines.push(`**🟢 GLM（思考+联网，中文语境）**`);
  lines.push(truncate(glm, 500));
  lines.push('');

  lines.push(`**🔷 Qwen 3.5 Plus（通义千问，阿里大模型）**`);
  lines.push(truncate(qwen, 500));
  lines.push('');

  lines.push(`---`);
  lines.push('');
  lines.push(`*以上为5个平台并行回复的综合整理，完整内容可在各自平台的对话窗口查看。*`);

  return lines.join('\n');
}

const question = process.argv.slice(2).join(' ');
if (!question) {
  console.error('用法: node zhiku-ask.js "<问题>"');
  process.exit(1);
}

main(question).catch(e => {
  console.error('Fatal:', e.message);
  process.exit(1);
});
