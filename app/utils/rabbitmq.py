import aio_pika

from app.core.settings import get_settings

# Initialize RabbitMQ connection
async def get_rabbitmq_connection():
    settings = get_settings()
    return await aio_pika.connect_robust(settings.RABBITMQ_URL)