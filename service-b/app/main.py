import os
from aio_pika import connect_robust
from aio_pika.abc import AbstractIncomingMessage
from contextlib import asynccontextmanager
from fastapi import FastAPI

RABBITMQ_URL = "amqp://{u}:{p}@{h}:{port}/".format(
    u=os.environ["RABBITMQ_USER"],
    p=os.environ["RABBITMQ_PASSWORD"],
    h=os.environ["RABBITMQ_HOST"],
    port=os.environ["RABBITMQ_PORT"],
)

QUEUE_NAME = os.environ.get("RABBITMQ_QUEUE", "demo")

async def handle_message(message: AbstractIncomingMessage):
    async with message.process():                  
        print(f"[service-b] received: {message.body.decode()}", flush=True)
        message = message.body.decode()        

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.mq = await connect_robust(RABBITMQ_URL)
    app.state.channel = await app.state.mq.channel()
    queue = await app.state.channel.declare_queue(QUEUE_NAME, durable=True)
    await queue.consume(handle_message)
    yield
    await app.state.mq.close()

app = FastAPI(title="service-b", version="0.1.0", lifespan=lifespan)

@app.get("/ping")
def read_root():
    return {"pong": "Hello world from service-b!"}


