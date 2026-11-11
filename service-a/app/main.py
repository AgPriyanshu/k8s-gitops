import os
import aio_pika
from contextlib import asynccontextmanager
from fastapi import FastAPI
from pydantic import BaseModel

RABBITMQ_URL = "amqp://{u}:{p}@{h}:{port}/".format(
    u=os.environ["RABBITMQ_USER"],
    p=os.environ["RABBITMQ_PASSWORD"],
    h=os.environ["RABBITMQ_HOST"],
    port=os.environ["RABBITMQ_PORT"],
)

QUEUE_NAME = os.environ.get("RABBITMQ_QUEUE", "demo")


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.mq = await aio_pika.connect_robust(RABBITMQ_URL)
    app.state.channel = await app.state.mq.channel()
    yield
    await app.state.mq.close()

app = FastAPI(title="service-a", lifespan=lifespan)

@app.get("/ping")
def read_root():
    return {"pong": "Hello world from service-a!"}

class PublishRequest(BaseModel):
    msg: str

@app.post("/publish")
async def publish(data: PublishRequest):
    await app.state.channel.default_exchange.publish(
        aio_pika.Message(body=data.msg.encode()), routing_key="demo"
    )
    
    return {"sent": data.msg}
