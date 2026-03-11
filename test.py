from google import genai

client = genai.Client()

response = client.models.generate_content(
    model="claude-sonnet-4-6",
    contents="你好"
)

print(response.text)