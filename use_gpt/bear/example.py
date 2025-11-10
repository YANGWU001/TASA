from openai import OpenAI


# endpoint : pluto jobs: http://pluto-prod-hawang-llm-proxy-9qtfav-0:4000
# key = sk-g-wO3D7N2V-VvcfhfqG9ww


# models:    
# claude-opus-4.1
# claude-sonnet-4
# claude-sonnet-4.5
# deepseek-r1
# gpt-3.5-turbo
# gpt-4.1
# gpt-4.1-mini
# gpt-4.1-nano
# gpt-4o
# gpt-4o-mini
# gpt-5
# gpt-5-chat
# gpt-5-mini
# gpt-5-nano
# gpt-image-1
# gpt-oss-120b
# gpt-oss-20b


endpoint = "<Insert your endpoint>" # Endpoint will be different depending on whether you will access from corp network (i.e. on your laptop in office or on VPN) or from pluto instances
key = "<Insert your key>" # e.g. sk-1234567890, to get one, use Slack command /get-llm-cred
model = "<Insert your model id>" # e.g llama-3-1-8b


# Initialize the client
client = OpenAI(
    api_key = "Bearer " + key,
    base_url = endpoint,
)

# Text input
chat_response = client.chat.completions.create(
    model = model,
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Tell me a joke."},
    ]
)

print("Chat response:", chat_response)

# Local image input - make sure the mime_type is consistent with the actual file
mime_type = "image/jpeg"
with open("your-image.jpeg", "rb") as f:
    b64_img = base64.b64encode(f.read()).decode('utf-8')

chat_response = client.chat.completions.create(
    model = model,
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": [
            {
              "type": "text",
              "text": f'What is in this image?'
            },
            {
              "type": "image_url",
              "image_url": {
                "url": f"data:{mime_type};base64,{b64_img}"
              }
            }
          ]},
    ]
)

print("Chat response:", chat_response)

# Get embeddings
response = client.embeddings.create(
    model="text-embedding-3-small", # or text-embedding-3-large
    input=[
        "first phrase",
        "second phrase",
        "third phrase",
    ],
)

for item in response.data:
    print(len(item.embedding), item.embedding[:3])