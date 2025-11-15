import redis
from dotenv import load_dotenv
import os

load_dotenv()  # loads .env into environment variables

REDIS_PORT = int(os.environ.get('REDIS_PORT', '6379'))

redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST'),
    port=REDIS_PORT,
    decode_responses=True
)