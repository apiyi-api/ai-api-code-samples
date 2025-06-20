from openai import OpenAI
from pydantic import BaseModel

# 初始化 APIYI 客户端
client = OpenAI(
    base_url="https://vip.apiyi.com/v1",
    api_key="sk-"  # 替换为你的实际 API Key
)

# 定义结构化输出的数据模型
class CalendarEvent(BaseModel):
    name: str
    date: str
    participants: list[str]

# 使用 APIYI 专用的 responses API
print("=== APIYI Responses API 结构化输出演示 ===")

try:
    response = client.responses.parse(
        model="gpt-4.1",
        input=[
            {"role": "system", "content": "Extract the event information."},
            {
                "role": "user",
                "content": "Alice and Bob are going to a science fair on Friday.",
            },
        ],
        text_format=CalendarEvent,
    )
    
    # 获取解析后的结构化结果
    event = response.output_parsed
    print("✅ 结构化输出成功:")
    print(f"  事件名称: {event.name}")
    print(f"  日期: {event.date}")
    print(f"  参与者: {event.participants}")
    print()
    print("完整结果:", event)
    
except Exception as e:
    print(f"❌ API调用失败: {type(e).__name__}: {e}")

print("\n=== APIYI Responses API 特点 ===")
print("• 使用方法: client.responses.parse()")
print("• 消息参数: input (而不是 messages)")
print("• 格式参数: text_format (而不是 response_format)")
print("• 结果获取: response.output_parsed")
print("• 自动解析: 直接返回 Pydantic 对象，无需手动 JSON 解析") 
