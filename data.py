"""Basic connection example.
"""

import redis

r = redis.Redis(
    host='xxxxx.ap-south-1-1.ec2.cloud.redislabs.com',
    port=18804,
    decode_responses=True,
    username="default",
    password="xxxxx",
)

success = r.set('foo', 'bar')
# True

result = r.get('foo')
print(result)
# >>> bar


