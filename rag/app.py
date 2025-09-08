import asyncio
import json
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
import uvicorn
from typing import Dict

KAFKA_BOOTSTRAP = "localhost:9092"
TOPIC_IN = "finance-chat-queries"
TOPIC_OUT = "finance-rag-results"

app = FastAPI()
producer: AIOKafkaProducer = None
consumer_task = None

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

latest_responses: Dict[str, dict] = {}

@app.on_event("startup")
async def startup():
    global producer, consumer_task
    loop = asyncio.get_running_loop()
    producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP)
    await producer.start()
    consumer_task = asyncio.create_task(consume_results())


@app.on_event("shutdown")
async def shutdown():
    global producer, consumer_task
    if consumer_task:
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass
    if producer:
        await producer.stop()


@app.post("/query")
async def send_query(payload: dict):
    user_id = payload.get("user_id", "anon")
    query_text = payload.get("query_text") or payload.get("message")
    if not query_text:
        return {"error": "query_text required"}
    message = {
        "user_id": user_id,
        "query_text": query_text,
        "timestamp_ms": int(asyncio.get_event_loop().time() * 1000)
    }
    await producer.send_and_wait(TOPIC_IN, json.dumps(message).encode("utf-8"))
    return {"status": "sent", "user_id": user_id}


async def consume_results():
    consumer = AIOKafkaConsumer(
        TOPIC_OUT,
        bootstrap_servers=KAFKA_BOOTSTRAP,
        group_id="fastapi-results-group",
        auto_offset_reset="earliest"
    )
    await consumer.start()
    try:
        async for msg in consumer:
            try:
                payload = json.loads(msg.value.decode("utf-8"))
            except Exception:
                payload = {"raw": msg.value.decode("utf-8")}
            user_id = payload.get("user_id", "anon")
            latest_responses[user_id] = payload
            print("Received from Flink:", payload)
    finally:
        await consumer.stop()


@app.get("/results/{user_id}")
async def get_result(user_id: str):
    if user_id in latest_responses:
        return latest_responses[user_id]
    return {"status": "no-result"}
    
if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
