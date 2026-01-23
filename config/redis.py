import os
import redis

redis_client = None

def init_redis():
    global redis_client

    redis_config = {
        'host': os.getenv('REDIS_HOST', 'localhost'),
        'port': int(os.getenv('REDIS_PORT', 6379)),
        'decode_responses': True
    }

    if os.getenv('REDIS_PASSWORD'):
        redis_config['password'] = os.getenv('REDIS_PASSWORD')

    redis_client = redis.Redis(**redis_config)

    # Test connection
    try:
        redis_client.ping()
        print('Redis Client Connected')
    except Exception as err:
        print(f'Redis Client Error: {err}')
        raise

    return redis_client

def get_redis_client():
    if not redis_client:
        raise Exception('Redis client not initialized')
    return redis_client
