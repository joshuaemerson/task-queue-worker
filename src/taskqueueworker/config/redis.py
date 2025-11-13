import redis
from dotenv import load_dotenv
import os

load_dotenv()  # loads .env into environment variables

redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST'),
    port=os.getenv('REDIS_PORT'),
    decode_responses=True
)