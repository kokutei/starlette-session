from starlette_session import RedisSessionHandler
import pickle

host = "localhost"
port = 6379


def test_redis_handler():

    test_redis_handler = RedisSessionHandler(host, port)

    session_id = test_redis_handler.create_session_id()

    session_data = {"key": "testdata"}

    test_redis_handler.open()
    test_redis_handler.write(session_id, pickle.dumps(session_data), 60 * 15)
    test_redis_handler.close()

    test_redis_handler.open()
    read_session_data = test_redis_handler.read(session_id)
    read_session_data = pickle.loads(read_session_data)
    assert session_data == read_session_data

    test_redis_handler.delete(session_id)
    read_session_data = test_redis_handler.read(session_id)

    assert read_session_data is None
