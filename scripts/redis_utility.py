from redis import StrictRedis
import time


def init_redis():
    cache = StrictRedis('localhost', 6379)
    if not cache.ping():
        raise
    pers = StrictRedis('localhost', 6380)
    if not pers.ping():
        raise
    return cache, pers


def test_get_set(r: StrictRedis):
    print('set prova test_key 1')
    print(r.set('test_key', 1))
    print('get test_key')
    print(type(r.get('test_key').decode('utf8')))


def test_zset(r: StrictRedis):
    print('zadd prova (now) one')
    print(type(r.zadd('prova', {'one': time.time()})))
    print('zadd prova (now) two')
    print(r.zadd('prova', {'two': time.time()}))
    print('zadd prova (now) three')
    print(r.zadd('prova', {'three': time.time()}))
    print('zrange prova 0 -1')
    print(r.zrange('prova', 0, -1))
    print('zcount prova 0 (now)')
    print(r.zcount('prova', 0, time.time()))

    print('zpopmin 2')
    print(r.zpopmin('prova', 2))
    print('zrange prova 0 -1')
    print(r.zrange('prova', 0, -1))
    print('zcount prova 0 (now)')
    print(r.zcount('prova', 0, time.time()))


if __name__ == '__main__':
    cache, pers = init_redis()
    test_get_set(cache)
