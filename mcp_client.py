import asyncio
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Union

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

load_dotenv()
llm = ChatOllama(
    model="qwen3:30b",
    base_url="http://192.168.100.202:11434",
    temperature=0,
    format="json"
)
server_params = StdioServerParameters(
    command="python", args=["./main.py"], env=None)


@dataclass
class Chat:
    messages: List[Union[HumanMessage, AIMessage,
                         SystemMessage]] = field(default_factory=list)
    system_prompt: str = """You are a master SQLite assistant. Your job is to use the tools at your disposal to execute SQL queries and provide the results to the user."""

    def __post_init__(self):
        self.messages.append(SystemMessage(content=self.system_prompt))

    async def process_query(self, session: ClientSession, query: str) -> None:
        # 获取可用工具
        response = await session.list_tools()
        print("response: ", response)
        available_tools = []
        for tool in response.tools:
            tool_info = {
                "name": tool.name,
                "description": tool.description or "",
                "parameters": tool.inputSchema
            }
            available_tools.append(tool_info)

        # 添加用户消息
        self.messages.append(HumanMessage(content=query))

        # 创建包含工具信息的提示
        tools_prompt = "\n".join([
            f"Tool: {tool['name']} - {tool['description']}\nParameters: {json.dumps(tool['parameters'], indent=2)}"
            for tool in available_tools
        ])

        enhanced_messages = self.messages.copy()
        if available_tools:
            tool_instruction = HumanMessage(content=f"""
Available tools:
{tools_prompt}

To use a tool, respond with JSON in this format:
{{"tool_name": "tool_name", "arguments": {{"param1": "value1", "param2": "value2"}}}}

If you don't need to use a tool, just respond normally.
Current query: {query}
""")
            enhanced_messages.append(tool_instruction)

        # 调用 LLM
        try:
            response = await llm.ainvoke(enhanced_messages)
            response_text = response.content

            # 检查是否需要调用工具
            if self._is_tool_call(response_text):
                await self._handle_tool_call(session, response_text, available_tools)
            else:
                print(response_text)
                self.messages.append(AIMessage(content=response_text))

        except Exception as e:
            print(f"Error calling LLM: {e}")

    def _is_tool_call(self, text: str) -> bool:
        """检查响应是否是工具调用"""
        try:
            parsed = json.loads(text.strip())
            return isinstance(parsed, dict) and "tool_name" in parsed and "arguments" in parsed
        except:
            print("not tool call")
            return False

    async def _handle_tool_call(self, session: ClientSession, response_text: str, available_tools: List[Dict]) -> None:
        """处理工具调用"""
        try:
            print("_handle_tool_call")
            tool_call = json.loads(response_text.strip())
            tool_name = tool_call["tool_name"]
            tool_args = tool_call["arguments"]

            print(f"Calling tool: {tool_name} with args: {tool_args}")

            # 调用 MCP 工具
            result = await session.call_tool(tool_name, tool_args)
            tool_result = ""
            if result.content:
                for content in result.content:
                    if hasattr(content, 'text'):
                        tool_result += content.text
                    elif hasattr(content, 'content'):
                        tool_result += str(content.content)
                    else:
                        tool_result += str(content)

            # 将工具调用和结果添加到消息历史
            self.messages.append(
                AIMessage(content=f"Tool call: {response_text}"))
            self.messages.append(HumanMessage(
                content=f"Tool result: {tool_result}"))

            # 让 LLM 处理工具结果
            final_response = await llm.ainvoke(self.messages + [
                HumanMessage(
                    content="Please provide a final response based on the tool result above.")
            ])

            print(final_response.content)
            self.messages.append(AIMessage(content=final_response.content))

        except Exception as e:
            print(f"Error handling tool call: {e}")
            self.messages.append(
                AIMessage(content=f"Error executing tool: {e}"))

    async def chat_loop(self, session: ClientSession):
        print("SQLite Assistant ready! Type your queries or 'quit' to exit.")
        while True:
            try:
                query = input("\nQuery: ").strip()
                if query.lower() in ['quit', 'exit']:
                    break
                if query:
                    await self.process_query(session, query)
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")

    async def run(self):
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                try:
                    await session.initialize()
                    await self.chat_loop(session)
                except Exception as e:
                    print(f"Session error: {e}")


if __name__ == "__main__":
    chat = Chat()
    asyncio.run(chat.run())
