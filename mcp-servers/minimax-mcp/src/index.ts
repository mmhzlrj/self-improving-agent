/**
 * MiniMax MCP Server
 * 
 * 提供两个工具:
 * 1. web_search - 使用 Brave Search API 进行网页搜索
 * 2. understand_image - 使用 MiniMax Vision API 分析图片
 * 
 * 环境变量:
 * - BRAVE_SEARCH_API_KEY: Brave Search API 密钥 (https://brave.com/search/api/)
 * - MINIMAX_API_KEY: MiniMax API 密钥 (https://platform.minimaxi.com/)
 * - MINIMAX_GROUP_ID: MiniMax Group ID
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import axios from 'axios';

// 环境变量
const BRAVE_SEARCH_API_KEY = process.env.BRAVE_SEARCH_API_KEY || '';
const MINIMAX_API_KEY = process.env.MINIMAX_API_KEY || '';
const MINIMAX_GROUP_ID = process.env.MINIMAX_GROUP_ID || '';

/**
 * 使用 Brave Search API 进行网页搜索
 */
async function braveSearch(query: string, count: number = 10) {
  if (!BRAVE_SEARCH_API_KEY) {
    throw new Error('BRAVE_SEARCH_API_KEY 环境变量未设置');
  }

  const response = await axios.get('https://api.search.brave.com/res/v1/web/search', {
    headers: {
      'Accept': 'application/json',
      'X-Subscription-Token': BRAVE_SEARCH_API_KEY,
    },
    params: {
      q: query,
      count: Math.min(count, 20),
    },
  });

  const results = response.data.web?.results || [];
  return results.map((item: any) => ({
    title: item.title,
    url: item.url,
    description: item.description,
  }));
}

/**
 * 使用 MiniMax Vision API 分析图片
 * 支持 base64 图片或 URL
 */
async function understandImage(imageInput: string, prompt: string = '请详细描述这张图片的内容') {
  if (!MINIMAX_API_KEY) {
    throw new Error('MINIMAX_API_KEY 环境变量未设置');
  }

  if (!MINIMAX_GROUP_ID) {
    throw new Error('MINIMAX_GROUP_ID 环境变量未设置');
  }

  // 判断是 URL 还是 base64
  let imageUrl = '';
  let imageBase64 = '';

  if (imageInput.startsWith('http://') || imageInput.startsWith('https://')) {
    imageUrl = imageInput;
  } else if (imageInput.startsWith('data:')) {
    // data:image/png;base64,xxx 格式
    const match = imageInput.match(/^data:image\/\w+;base64,(.+)$/);
    if (match) {
      imageBase64 = match[1];
    }
  } else if (/^[A-Za-z0-9+/=]+$/.test(imageInput) && imageInput.length > 100) {
    // 可能是纯 base64
    imageBase64 = imageInput;
  } else {
    throw new Error('图片输入必须是 URL 或 base64 格式');
  }

  // 构建请求
  const messages: any[] = [
    {
      role: 'user',
      content: [
        {
          type: 'text',
          text: prompt,
        },
      ],
    },
  ];

  // 添加图片
  if (imageUrl) {
    messages[0].content.push({
      type: 'image_url',
      image_url: {
        url: imageUrl,
      },
    });
  } else if (imageBase64) {
    messages[0].content.push({
      type: 'image_url',
      image_url: {
        url: `data:image/jpeg;base64,${imageBase64}`,
      },
    });
  }

  const response = await axios.post(
    'https://api.minimax.chat/v1/text/chatcompletion_v2',
    {
      model: 'MiniMax-Vision',
      messages,
      temperature: 0.7,
    },
    {
      headers: {
        'Authorization': `Bearer ${MINIMAX_API_KEY}`,
        'Content-Type': 'application/json',
      },
      params: {
        GroupId: MINIMAX_GROUP_ID,
      },
    }
  );

  if (response.data?.choices?.[0]?.message?.content) {
    return response.data.choices[0].message.content;
  }

  return response.data;
}

// MCP Server 实现
class MiniMaxMCPServer {
  private server: Server;

  constructor() {
    this.server = new Server(
      {
        name: 'minimax-mcp',
        version: '1.0.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.setupHandlers();
  }

  private setupHandlers() {
    // 列出可用工具
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: [
          {
            name: 'web_search',
            description: '使用 Brave Search API 进行网页搜索',
            inputSchema: {
              type: 'object',
              properties: {
                query: {
                  type: 'string',
                  description: '搜索关键词',
                },
                count: {
                  type: 'number',
                  description: '返回结果数量 (默认 10, 最大 20)',
                  default: 10,
                },
              },
              required: ['query'],
            },
          },
          {
            name: 'understand_image',
            description: '使用 MiniMax Vision API 分析图片内容',
            inputSchema: {
              type: 'object',
              properties: {
                image: {
                  type: 'string',
                  description: '图片 URL 或 base64 编码',
                },
                prompt: {
                  type: 'string',
                  description: '分析提示词 (默认: "请详细描述这张图片的内容")',
                  default: '请详细描述这张图片的内容',
                },
              },
              required: ['image'],
            },
          },
        ],
      };
    });

    // 处理工具调用
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      if (!args) {
        return {
          content: [{ type: 'text', text: '错误: 缺少参数' }],
          isError: true,
        };
      }

      try {
        if (name === 'web_search') {
          const results = await braveSearch(args.query as string, args.count as number | undefined);
          return {
            content: [
              {
                type: 'text',
                text: JSON.stringify(results, null, 2),
              },
            ],
          };
        }

        if (name === 'understand_image') {
          const result = await understandImage(
            args.image as string,
            args.prompt as string | undefined
          );
          return {
            content: [
              {
                type: 'text',
                text: result,
              },
            ],
          };
        }

        throw new Error(`未知工具: ${name}`);
      } catch (error: any) {
        return {
          content: [
            {
              type: 'text',
              text: `错误: ${error.message}`,
            },
          ],
          isError: true,
        };
      }
    });
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('MiniMax MCP Server 已启动');
  }
}

// 启动服务器
const server = new MiniMaxMCPServer();
server.run().catch(console.error);
