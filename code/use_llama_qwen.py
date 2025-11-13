import asyncio
import httpx


llama_url = "https://e9e2775be0da.ngrok-free.app/predict/"
qwen_url = "https://d53740ee5f4b.ngrok-free.app/predict/"

async def call_api(i):
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            qwen_url,
            json={
                "system_prompt": "You are a helpful assistant.",
                "user_prompt": f"Write a short poem about thread {i}."
            },
            timeout=60
        )
        print(f"Response {i}: {resp.json()['result'][:100]}...")

async def main():
    tasks = [call_api(i) for i in range(40)]
    await asyncio.gather(*tasks)

asyncio.run(main())
