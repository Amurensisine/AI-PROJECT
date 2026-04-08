"""
本地快速测试脚本 —— 直接用 AnthropicVertex 调用 Claude
使用前请确保已设置：
  export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your-key.json"
  export GOOGLE_CLOUD_PROJECT="your-project-id"
"""

import os
from anthropic import AnthropicVertex

PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "ai-project-489913")
REGION = "us-east5"
MODEL = "claude-3-5-sonnet-v2@20241022"

client = AnthropicVertex(project_id=PROJECT_ID, region=REGION)

response = client.messages.create(
    model=MODEL,
    max_tokens=256,
    messages=[{"role": "user", "content": "你好，请用一句话介绍你自己。"}],
)

print(response.content[0].text)
