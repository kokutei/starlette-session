from typing import Dict, Text
import uuid
from redis.client import Redis
from ..session import SessionHandler, DEFAULT_SESSION_NAME


class RedisSessionHandler(SessionHandler):
    """
    Redis session data storage handler
    """

    redis: Redis = None
    
    def __init__(
        self,
        host: str,
        port: int,
        db: int = 0,
        password: Text = None,
        options: Dict = {},
        key_prefix=DEFAULT_SESSION_NAME,
    ) -> None:
        super().__init__()

        if not options:
            options = {}

        options["host"] = host
        options["port"] = port
        options["db"] = db

        if password:
            options["password"] = password

        self.options = options
        # self.redis = Redis(**options)

        self.key_prefix = key_prefix

    def create_session_id(self) -> str:
        return uuid.uuid4().hex

    def read(self, session_id: str) -> str:
        self.open()
        return self.redis.get(self.__key_session_id(session_id))

    def write(self, session_id: str, data: str, expire: int) -> str:
        self.open()
        return self.redis.set(self.__key_session_id(session_id), data, ex=expire)

    def delete(self, session_id):
        self.open()
        key=self.__key_session_id(session_id)        
        self.redis.delete(key)        

    def open(self):
        if not self.redis:           
            self.redis = Redis(**self.options)
        return

    def close(self):
        if self.redis:            
            self.redis.close()        
            self.redis = None
        return

    def __key_session_id(self, session_id: str) -> str:
        return self.key_prefix + session_id
