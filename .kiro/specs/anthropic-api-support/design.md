# Anthropic API 支持设计文档

## 概述

本设计文档描述了如何在现有的 Ki2API 项目中添加对 Anthropic API 格式的支持。设计目标是在保持现有 OpenAI API 功能的同时，增加对 Anthropic Messages API 的完整支持，包括内容块系统、工具调用和流式响应。

## 架构

### 整体架构图

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│   Client        │    │   Ki2API         │    │  AWS CodeWhisperer  │
│                 │    │                  │    │                     │
│ OpenAI Format   │───▶│  Format Router   │───▶│   Unified Backend   │
│ Anthropic Format│───▶│  & Converter     │───▶│                     │
└─────────────────┘    └──────────────────┘    └─────────────────────┘
```

### 请求处理流程

```
Request → Format Detection → Request Conversion → CodeWhisperer API → Response Conversion → Client
```

## 组件和接口

### 1. 代码结构重构

#### 文件组织结构
```
src/kiro2api/
├── app.py                 # 主应用入口和路由
├── common/
│   ├── __init__.py
│   ├── models.py          # 公共数据模型
│   ├── auth.py            # 认证相关
│   ├── token_manager.py   # Token 管理
│   ├── codewhisperer.py   # CodeWhisperer 客户端
│   └── utils.py           # 工具函数
├── openai/
│   ├── __init__.py
│   ├── models.py          # OpenAI 特定数据模型
│   ├── handlers.py        # OpenAI API 处理器
│   ├── converters.py      # OpenAI 格式转换器
│   └── streaming.py       # OpenAI 流式处理
└── anthropic/
    ├── __init__.py
    ├── models.py          # Anthropic 特定数据模型
    ├── handlers.py        # Anthropic API 处理器
    ├── converters.py      # Anthropic 格式转换器
    └── streaming.py       # Anthropic 流式处理
```

#### 主应用文件 (app.py)
```python
from fastapi import FastAPI
from .common.auth import verify_api_key
from .openai.handlers import openai_router
from .anthropic.handlers import anthropic_router

app = FastAPI(...)

# 注册路由
app.include_router(openai_router, prefix="/v1")
app.include_router(anthropic_router, prefix="/v1")

# 公共端点
@app.get("/health")
@app.get("/")
@app.get("/v1/models")
```

### 2. API 路由层

#### 路由分离
- `openai_router`: 处理 `/v1/chat/completions` 端点
- `anthropic_router`: 处理 `/v1/messages` 端点
- 公共路由: `/health`, `/`, `/v1/models`

### 3. 公共组件设计

#### common/models.py - 公共数据模型
```python
# 从现有 app.py 提取的公共模型
class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

class ToolCall(BaseModel):
    id: str
    type: str = "function"
    function: Dict[str, Any]

# CodeWhisperer 相关模型
class CodeWhispererRequest(BaseModel):
    profileArn: str
    conversationState: Dict[str, Any]

class CodeWhispererResponse(BaseModel):
    # CodeWhisperer 响应格式
    pass
```

#### common/token_manager.py - Token 管理
```python
# 从现有 app.py 提取 TokenManager 类
class TokenManager:
    async def refresh_tokens(self) -> Optional[str]
    def get_token(self) -> str
```

#### common/codewhisperer.py - CodeWhisperer 客户端
```python
# 从现有 app.py 提取 API 调用逻辑
class CodeWhispererClient:
    async def call_api(self, request_data: Dict) -> httpx.Response
    async def call_streaming_api(self, request_data: Dict) -> httpx.Response
```

#### common/auth.py - 认证
```python
# 从现有 app.py 提取认证逻辑
async def verify_api_key(authorization: str = Header(None)) -> str
```

### 4. 数据模型层

#### OpenAI API 数据模型 (openai/models.py)
```python
# 从现有 app.py 提取的 OpenAI 模型
class ChatMessage(BaseModel):
    role: str
    content: Union[str, List[ContentPart], None]
    tool_calls: Optional[List[ToolCall]] = None
    tool_call_id: Optional[str] = None

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 4000
    stream: Optional[bool] = False
    # ... 其他 OpenAI 参数

class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Choice]
    usage: Usage
```

#### Anthropic API 数据模型 (anthropic/models.py)

```python
class AnthropicContentBlock(BaseModel):
    type: Literal["text", "image", "tool_use", "tool_result"]
    # 根据 type 的不同，包含不同的字段

class AnthropicTextBlock(AnthropicContentBlock):
    type: Literal["text"] = "text"
    text: str

class AnthropicImageBlock(AnthropicContentBlock):
    type: Literal["image"] = "image"
    source: Dict[str, Any]  # {"type": "base64", "media_type": "image/jpeg", "data": "..."}

class AnthropicToolUseBlock(AnthropicContentBlock):
    type: Literal["tool_use"] = "tool_use"
    id: str
    name: str
    input: Dict[str, Any]

class AnthropicToolResultBlock(AnthropicContentBlock):
    type: Literal["tool_result"] = "tool_result"
    tool_use_id: str
    content: Union[str, List[AnthropicContentBlock]]
    is_error: Optional[bool] = False

class AnthropicMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: Union[str, List[AnthropicContentBlock]]

class AnthropicMessagesRequest(BaseModel):
    model: str
    max_tokens: int
    messages: List[AnthropicMessage]
    system: Optional[Union[str, List[Dict[str, Any]]]] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    stop_sequences: Optional[List[str]] = None
    stream: Optional[bool] = False
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[Union[str, Dict[str, Any]]] = None

class AnthropicMessagesResponse(BaseModel):
    id: str
    type: Literal["message"] = "message"
    role: Literal["assistant"] = "assistant"
    content: List[AnthropicContentBlock]
    model: str
    stop_reason: Optional[Literal["end_turn", "max_tokens", "stop_sequence", "tool_use"]]
    stop_sequence: Optional[str] = None
    usage: Dict[str, int]  # {"input_tokens": 123, "output_tokens": 456}
```

### 5. 处理器层

#### OpenAI 处理器 (openai/handlers.py)
```python
from fastapi import APIRouter
from .models import ChatCompletionRequest, ChatCompletionResponse
from .converters import OpenAIToCodeWhispererConverter
from ..common.codewhisperer import CodeWhispererClient

openai_router = APIRouter()

@openai_router.post("/chat/completions")
async def create_chat_completion(request: ChatCompletionRequest):
    # 从现有 app.py 提取的处理逻辑
    pass
```

#### Anthropic 处理器 (anthropic/handlers.py)
```python
from fastapi import APIRouter
from .models import AnthropicMessagesRequest, AnthropicMessagesResponse
from .converters import AnthropicToCodeWhispererConverter
from ..common.codewhisperer import CodeWhispererClient

anthropic_router = APIRouter()

@anthropic_router.post("/messages")
async def create_message(request: AnthropicMessagesRequest):
    # 新的 Anthropic API 处理逻辑
    pass
```

### 6. 格式转换层

#### OpenAI 转换器 (openai/converters.py)
```python
# 从现有 app.py 提取的转换逻辑
class OpenAIToCodeWhispererConverter:
    def convert_request(self, openai_request: ChatCompletionRequest) -> Dict[str, Any]:
        """将 OpenAI 请求转换为 CodeWhisperer 格式"""
        # 现有的 build_codewhisperer_request 逻辑
        
class CodeWhispererToOpenAIConverter:
    def convert_response(self, cw_response: str, original_request: ChatCompletionRequest) -> ChatCompletionResponse:
        """将 CodeWhisperer 响应转换为 OpenAI 格式"""
        # 现有的响应转换逻辑
```

#### Anthropic 转换器 (anthropic/converters.py)
```python
class AnthropicToCodeWhispererConverter:
    def convert_request(self, anthropic_request: AnthropicMessagesRequest) -> Dict[str, Any]:
        """将 Anthropic 请求转换为 CodeWhisperer 格式"""
        
    def convert_messages(self, messages: List[AnthropicMessage]) -> Tuple[str, List[Dict]]:
        """转换消息格式，返回 (system_prompt, conversation_messages)"""
        
    def convert_tools(self, tools: List[Dict]) -> List[Dict]:
        """转换工具定义格式"""
        
    def convert_content_blocks(self, content: Union[str, List[AnthropicContentBlock]]) -> Tuple[str, List[Dict]]:
        """转换内容块，返回 (text_content, images)"""

class CodeWhispererToAnthropicConverter:
    def convert_response(self, cw_response: str, original_request: AnthropicMessagesRequest) -> AnthropicMessagesResponse:
        """将 CodeWhisperer 响应转换为 Anthropic 格式"""
        
    def convert_tool_calls_to_blocks(self, tool_calls: List[ToolCall]) -> List[AnthropicToolUseBlock]:
        """将工具调用转换为 Anthropic tool_use 块"""
        
    def convert_text_to_blocks(self, text: str) -> List[AnthropicTextBlock]:
        """将文本转换为 Anthropic text 块"""
```

### 7. 流式响应处理

#### OpenAI 流式处理 (openai/streaming.py)
```python
# 从现有 app.py 提取的流式处理逻辑
class OpenAIStreamProcessor:
    async def create_streaming_response(self, request: ChatCompletionRequest) -> StreamingResponse:
        # 现有的流式响应逻辑
        pass
        
    async def convert_to_streaming_response(self, response: ChatCompletionResponse) -> StreamingResponse:
        # 现有的非流式到流式转换逻辑
        pass
```

#### Anthropic 流式事件格式

```python
class AnthropicStreamEvent(BaseModel):
    type: str
    
class MessageStartEvent(AnthropicStreamEvent):
    type: Literal["message_start"] = "message_start"
    message: Dict[str, Any]

class ContentBlockStartEvent(AnthropicStreamEvent):
    type: Literal["content_block_start"] = "content_block_start"
    index: int
    content_block: Dict[str, Any]

class ContentBlockDeltaEvent(AnthropicStreamEvent):
    type: Literal["content_block_delta"] = "content_block_delta"
    index: int
    delta: Dict[str, Any]

class ContentBlockStopEvent(AnthropicStreamEvent):
    type: Literal["content_block_stop"] = "content_block_stop"
    index: int

class MessageDeltaEvent(AnthropicStreamEvent):
    type: Literal["message_delta"] = "message_delta"
    delta: Dict[str, Any]
    usage: Dict[str, int]

class MessageStopEvent(AnthropicStreamEvent):
    type: Literal["message_stop"] = "message_stop"
```

#### Anthropic 流式处理 (anthropic/streaming.py)
```python
class AnthropicStreamProcessor:
    async def create_streaming_response(self, request: AnthropicMessagesRequest) -> StreamingResponse:
        """创建 Anthropic 格式的流式响应"""
        
    def convert_codewhisperer_stream_to_anthropic(self, cw_events: Iterator[Dict]) -> Iterator[str]:
        """将 CodeWhisperer 流式事件转换为 Anthropic SSE 格式"""
```

### 8. 模型映射

#### 统一模型映射 (common/models.py)
```python
# 现有的 OpenAI 模型映射
OPENAI_MODEL_MAP = {
    "claude-sonnet-4-20250514": "CLAUDE_SONNET_4_20250514_V1_0",
    "claude-3-5-haiku-20241022": "CLAUDE_3_7_SONNET_20250219_V1_0",
}

# 新增的 Anthropic 模型映射

```python
ANTHROPIC_MODEL_MAP = {
    # Anthropic 模型名 -> CodeWhisperer 模型名
    "claude-3-5-sonnet-20241022": "CLAUDE_SONNET_4_20250514_V1_0",
    "claude-3-5-haiku-20241022": "CLAUDE_3_7_SONNET_20250219_V1_0",
    "claude-3-sonnet-20240229": "CLAUDE_SONNET_4_20250514_V1_0",
    "claude-3-haiku-20240307": "CLAUDE_3_7_SONNET_20250219_V1_0",
}

def map_anthropic_model(anthropic_model: str) -> str:
    """映射 Anthropic 模型名到 CodeWhisperer 模型名"""
```

## 数据模型

### 内容块处理策略

1. **文本块**: 直接提取文本内容
2. **图片块**: 转换 base64 数据和 media_type 到 CodeWhisperer 格式
3. **工具使用块**: 转换为 CodeWhisperer 工具调用格式
4. **工具结果块**: 格式化为工具执行结果文本

### 消息角色映射

- Anthropic `user` → CodeWhisperer `user`
- Anthropic `assistant` → CodeWhisperer `assistant`
- 工具结果自动合并到下一个用户消息中

## 错误处理

### 错误响应格式

```python
class AnthropicErrorResponse(BaseModel):
    type: Literal["error"] = "error"
    error: Dict[str, Any]

# 示例错误格式
{
    "type": "error",
    "error": {
        "type": "invalid_request_error",
        "message": "Missing required parameter: max_tokens"
    }
}
```

### 错误类型映射

- 请求验证错误 → `invalid_request_error`
- 认证错误 → `authentication_error`
- 权限错误 → `permission_error`
- 速率限制 → `rate_limit_error`
- API 错误 → `api_error`

## 测试策略

### 单元测试

1. **格式转换测试**
   - Anthropic → CodeWhisperer 请求转换
   - CodeWhisperer → Anthropic 响应转换
   - 内容块处理测试

2. **模型映射测试**
   - 支持的模型映射
   - 不支持模型的错误处理

3. **验证测试**
   - 必需参数验证
   - 参数范围验证
   - 消息格式验证

### 集成测试

1. **端到端测试**
   - 完整的 Anthropic API 请求流程
   - 流式响应测试
   - 工具调用测试

2. **兼容性测试**
   - 与现有 OpenAI API 的兼容性
   - 多格式并发处理

### 性能测试

1. **响应时间测试**
   - 格式转换开销
   - 流式响应延迟

2. **并发测试**
   - 多格式请求并发处理
   - 资源使用情况

## 重构策略

### 代码迁移计划

1. **第一阶段**: 提取公共组件
   - 创建 `common/` 目录结构
   - 提取 TokenManager, 认证, CodeWhisperer 客户端
   - 提取公共数据模型和工具函数

2. **第二阶段**: 重构 OpenAI 处理
   - 创建 `openai/` 目录结构
   - 将现有 OpenAI 逻辑迁移到专门的模块
   - 确保功能完全兼容

3. **第三阶段**: 实现 Anthropic 支持
   - 创建 `anthropic/` 目录结构
   - 实现 Anthropic API 处理逻辑
   - 添加格式转换和流式处理

4. **第四阶段**: 集成和测试
   - 更新主应用文件
   - 集成测试和性能优化
   - 文档更新

## 部署考虑

### 配置更新

- 无需新增环境变量
- 复用现有的认证和配置系统
- 模块化设计便于维护和扩展

### 向后兼容性

- 现有 OpenAI API 端点保持不变
- 现有客户端代码无需修改
- 重构过程中保持 API 接口稳定

### 监控和日志

- 添加模块级别的日志标识
- 监控两种格式的使用情况和性能指标
- 独立的错误处理和监控

## 安全考虑

### 输入验证

- 严格验证 Anthropic API 请求格式
- 防止恶意内容块注入
- 图片数据大小限制

### 认证授权

- 复用现有的 API Key 认证机制
- 支持相同的访问控制策略