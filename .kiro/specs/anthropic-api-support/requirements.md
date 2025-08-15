# Anthropic API 支持需求文档

## 介绍

为 Ki2API 项目增加对 Anthropic API 格式请求的支持，使其能够同时处理 OpenAI 和 Anthropic 两种 API 格式的请求，并将它们统一转换为 AWS CodeWhisperer 服务所需的格式。

基于 Anthropic API 官方文档 (https://docs.anthropic.com/en/api/overview)，需要支持以下核心功能：
- Messages API (`POST /v1/messages`)
- 内容块系统 (text, image, tool_use, tool_result)
- 流式响应 (Server-Sent Events)
- 工具调用 (Function calling)
- 多模态输入 (文本 + 图片)

## 需求

### 需求 1: Anthropic API 格式支持

**用户故事:** 作为开发者，我希望能够使用 Anthropic API 格式发送请求到 Ki2API，这样我就可以在不修改现有 Anthropic 集成代码的情况下使用 Claude Sonnet 4。

#### 验收标准

1. WHEN 用户发送 Anthropic 格式的 `POST /v1/messages` 请求 THEN 系统 SHALL 正确解析请求参数
2. WHEN 请求包含 `model` 参数 THEN 系统 SHALL 将 Anthropic 模型名映射到对应的 CodeWhisperer 模型
3. WHEN 请求包含 `system` 参数（字符串或对象数组）THEN 系统 SHALL 将其转换为适当的系统提示词
4. WHEN 请求包含 `messages` 数组 THEN 系统 SHALL 正确处理 user/assistant 角色和内容块
5. WHEN 请求包含 `max_tokens` 参数 THEN 系统 SHALL 将其映射到相应的 CodeWhisperer 参数
6. WHEN 请求包含 `temperature`、`top_p`、`top_k` 参数 THEN 系统 SHALL 将其传递给底层服务
7. WHEN 请求包含 `stream: true` THEN 系统 SHALL 返回 Server-Sent Events 格式的流式响应
8. WHEN 请求包含 `stop_sequences` THEN 系统 SHALL 将其转换为适当的停止条件

### 需求 2: 内容块处理

**用户故事:** 作为开发者，我希望能够使用 Anthropic 的内容块格式发送复杂消息，包括文本、图片和工具调用。

#### 验收标准

1. WHEN 消息包含 `text` 类型内容块 THEN 系统 SHALL 正确提取文本内容
2. WHEN 消息包含 `image` 类型内容块 THEN 系统 SHALL 正确处理图片数据和 media_type
3. WHEN 消息包含 `tool_use` 类型内容块 THEN 系统 SHALL 将其转换为 CodeWhisperer 工具调用格式
4. WHEN 消息包含 `tool_result` 类型内容块 THEN 系统 SHALL 正确处理工具执行结果
5. WHEN 单个消息包含多个内容块 THEN 系统 SHALL 保持内容块的顺序和关联性

### 需求 3: 工具调用格式转换

**用户故事:** 作为开发者，我希望在使用 Anthropic API 格式时也能使用工具调用功能，这样我就可以保持与 Anthropic Claude API 的完全兼容性。

#### 验收标准

1. WHEN Anthropic 请求包含 `tools` 参数 THEN 系统 SHALL 将工具定义转换为 CodeWhisperer 格式
2. WHEN 请求包含 `tool_choice` 参数（auto/any/tool对象）THEN 系统 SHALL 正确处理工具选择策略
3. WHEN 响应包含工具调用 THEN 系统 SHALL 将其转换为 Anthropic 格式的 `tool_use` 内容块
4. WHEN 请求包含 `tool_result` 内容块 THEN 系统 SHALL 正确处理工具执行结果并传递给 CodeWhisperer

### 需求 4: 响应格式转换

**用户故事:** 作为开发者，我希望收到标准的 Anthropic API 格式响应，这样我的现有代码就不需要修改。

#### 验收标准

1. WHEN 系统处理 Anthropic 格式请求 THEN 响应 SHALL 符合 Anthropic Messages API 规范
2. WHEN 响应包含文本内容 THEN 系统 SHALL 使用 `text` 类型的内容块格式：`{"type": "text", "text": "content"}`
3. WHEN 响应包含工具调用 THEN 系统 SHALL 使用 `tool_use` 类型的内容块格式：`{"type": "tool_use", "id": "...", "name": "...", "input": {...}}`
4. WHEN 请求是流式的 THEN 系统 SHALL 返回 SSE 格式的流式响应，包含 `message_start`, `content_block_start`, `content_block_delta`, `content_block_stop`, `message_delta`, `message_stop` 事件
5. WHEN 响应完成 THEN 系统 SHALL 包含正确的 `usage` 信息（input_tokens, output_tokens）
6. WHEN 响应包含 `stop_reason` THEN 系统 SHALL 使用正确的值：`end_turn`, `max_tokens`, `stop_sequence`, `tool_use`

### 需求 5: 图片处理兼容性

**用户故事:** 作为开发者，我希望能够使用 Anthropic 的图片格式发送图片，这样我就可以进行多模态对话。

#### 验收标准

1. WHEN 请求包含 `image` 类型的内容块 THEN 系统 SHALL 正确解析图片数据
2. WHEN 图片使用 base64 编码 THEN 系统 SHALL 将其转换为 CodeWhisperer 所需格式
3. WHEN 图片包含 media_type 信息 THEN 系统 SHALL 正确识别图片格式
4. WHEN 处理多个图片 THEN 系统 SHALL 保持图片顺序和关联性

### 需求 6: 错误处理和兼容性

**用户故事:** 作为开发者，我希望在使用 Anthropic API 格式时能够收到适当的错误信息，这样我就可以正确处理异常情况。

#### 验收标准

1. WHEN 请求格式不正确 THEN 系统 SHALL 返回 Anthropic 格式的错误响应
2. WHEN 模型不支持 THEN 系统 SHALL 返回适当的错误信息
3. WHEN 认证失败 THEN 系统 SHALL 返回标准的认证错误
4. WHEN 服务不可用 THEN 系统 SHALL 返回适当的服务错误

### 需求 7: API 端点路由

**用户故事:** 作为开发者，我希望能够通过标准的 Anthropic API 端点访问服务，这样我就可以最小化代码修改。

#### 验收标准

1. WHEN 用户访问 `/v1/messages` 端点 THEN 系统 SHALL 识别为 Anthropic 格式请求
2. WHEN 用户访问 `/v1/chat/completions` 端点 THEN 系统 SHALL 识别为 OpenAI 格式请求
3. WHEN 系统检测到请求格式 THEN 系统 SHALL 自动选择相应的处理逻辑
4. WHEN 响应格式确定 THEN 系统 SHALL 使用对应的响应模型

### 需求 8: 模型映射和兼容性

**用户故事:** 作为开发者，我希望能够使用 Anthropic 的模型名称，系统自动映射到可用的 CodeWhisperer 模型。

#### 验收标准

1. WHEN 请求指定 `claude-3-5-sonnet-20241022` THEN 系统 SHALL 映射到 `CLAUDE_SONNET_4_20250514_V1_0`
2. WHEN 请求指定 `claude-3-5-haiku-20241022` THEN 系统 SHALL 映射到 `CLAUDE_3_7_SONNET_20250219_V1_0`
3. WHEN 请求指定 `claude-3-sonnet-20240229` THEN 系统 SHALL 映射到合适的 CodeWhisperer 模型
4. WHEN 请求指定不支持的模型 THEN 系统 SHALL 返回 400 错误和适当的错误信息
5. WHEN 模型映射完成 THEN 系统 SHALL 在响应中返回原始请求的模型名称

### 需求 9: 请求验证和限制

**用户故事:** 作为系统管理员，我希望系统能够正确验证 Anthropic API 请求的格式和参数，确保服务的稳定性。

#### 验收标准

1. WHEN 请求缺少必需的 `model` 参数 THEN 系统 SHALL 返回 400 错误
2. WHEN 请求缺少必需的 `messages` 参数 THEN 系统 SHALL 返回 400 错误  
3. WHEN 请求缺少必需的 `max_tokens` 参数 THEN 系统 SHALL 返回 400 错误
4. WHEN `max_tokens` 超过模型限制 THEN 系统 SHALL 返回适当的错误信息
5. WHEN `messages` 数组为空 THEN 系统 SHALL 返回 400 错误
6. WHEN 最后一条消息不是 `user` 角色 THEN 系统 SHALL 返回 400 错误（除非包含 tool_result）