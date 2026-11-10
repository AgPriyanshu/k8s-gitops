import os
import aio_pika
from contextlib import asynccontextmanager
from fastapi import FastAPI

RABBITMQ_URL = "amqp://{u}:{p}@{h}:{port}/".format(
    u=os.environ["RABBITMQ_USER"],
    p=os.environ["RABBITMQ_PASSWORD"],
    h=os.environ["RABBITMQ_HOST"],
    port=os.environ["RABBITMQ_PORT"],
)

QUEUE_NAME = os.environ.get("RABBITMQ_QUEUE", "demo")

async def handle_message(message: aio_pika.abc.AbstractIncomingMessage):
    async with message.process():  # ack on success, reject on exception
        print(f"[service-a] received: {message.body.decode()}", flush=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.mq = await aio_pika.connect_robust(RABBITMQ_URL)
    app.state.channel = await app.state.mq.channel()
    queue = await app.state.channel.declare_queue(QUEUE_NAME, durable=True)
    await queue.consume(handle_message)
    yield
    await app.state.mq.close()

app = FastAPI(title="service-a", lifespan=lifespan)

@app.get("/ping")
def read_root():
    return {"pong": "Hello world from service-a!"}

@app.post("/publish")
async def publish(msg: str):
    await app.state.channel.default_exchange.publish(
        aio_pika.Message(body=msg.encode()), routing_key="demo"
    )
    
    return {"sent": msg}
