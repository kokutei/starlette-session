from abc import ABC, abstractmethod
from typing import Any, Optional
import time
from starlette.datastructures import MutableHeaders
from starlette.requests import HTTPConnection
from starlette.types import ASGIApp, Message, Receive, Scope, Send
import pickle

DEFAULT_SESSION_NAME = "PYSESSONID"


class SessionHandler(ABC):
    def create_session_id(self) -> str:
        """
        Generates and returns a new session ID.
        """
        pass

    @abstractmethod
    def read(self, session_id: str) -> str:
        pass

    @abstractmethod
    def write(self, session_id: str, data: str, expire: int):
        pass

    @abstractmethod
    def close(self):
        pass

    @abstractmethod
    def delete(self, session_id: str):
        pass


class HTTPSession:

    __is_new = False
    __is_started = False
    __is_destoried = False
    __session_data = {}

    def __init__(
        self,
        connection: HTTPConnection,
        handler: SessionHandler,
        cookie_expire: int = 0,
        gc_lifetime: int = 1800,
        session_id: str = None,
        session_name: str = DEFAULT_SESSION_NAME,
    ):
        self.connection = connection
        self.handler = handler
        self.cookie_expire = cookie_expire
        self.gc_lifetime = gc_lifetime
        self.session_id = session_id
        self.session_name = session_name
        self.session_id = connection.cookies.get(session_name)

    def start(self, create: bool = False) -> bool:

        if self.__is_started:
            return True        
        
        if not self.session_id:
            if not create:
                return False
            else:
                self.__is_new = True
                self.session_id = self.handler.create_session_id()
        else:
            try:
                session_data = self.handler.read(self.session_id)
                if session_data:
                    session_data = pickle.loads(session_data)
                    if session_data:
                        self.__session_data.update(session_data)
            except pickle.PickleError as e:
                print(e)
        
        self.__is_started = True
        return True

    def is_new(self):
        return self.__is_new
        
    def keys(self):
        return self.__session_data.keys()

    def get(self, key: str, default: Any = None):
        return self.__session_data.get(key, default)

    def set(self, key: str, value: Any):
        self.__session_data[key] = value

    def regenerate_session_id(self, delete_old_session: False):

        new_session_id = self.handler.create_session_id()

        if delete_old_session and self.session_id:
            self.__session_data = {}
            self.handler.delete(self.session_id)

        self.session_id = new_session_id
        self.__is_new = True

    def close(self):

        if self.__is_started:
            session_data = pickle.dumps(self.__session_data)
            self.handler.write(self.session_id, session_data, self.gc_lifetime)
            self.__is_started = False

        self.handler.close()

    def destory(self):
        
        if self.session_id:        
            self.handler.delete(self.session_id)
            self.__session_data = {}
            self.__is_destoried = True
            self.__is_new = False
            self.__is_started = False

    def should_send_cookie(self) -> bool:

        if not self.session_id:
            return False

        if self.__is_destoried:
            return True

        if self.__is_new:
            return True

        if self.cookie_expire != 0:
            return True

    def is_destoried(self) -> bool:
        return self.__is_destoried


class SessionMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        session_name: str = DEFAULT_SESSION_NAME,  # The name of the current session. will be used as cookie name
        cookie_path: str = "/",  # cookie path
        cookie_domain: Optional[str] = None,  # cookie domain
        cookie_expire: int = 0,  # cookie expire. The value 0 means "until the browser is closed."
        cookie_httponly: bool = True,
        cookie_secure: bool = False,
        cookie_samesite: str = "Lax",
        session_handler: SessionHandler = None,
        # The number of seconds after which data will be seen as 'garbage' and potentially cleaned up
        gc_lifetime: int = 30 * 60,
    ):
        self.app = app
        self.session_name = session_name
        self.cookie_path = cookie_path
        self.cookie_domain = cookie_domain
        self.cookie_expire = cookie_expire
        self.gc_lifetime = gc_lifetime
        self.cookie_httponly = cookie_httponly
        self.cookie_secure = cookie_secure
        self.cookie_samesite = cookie_samesite
        self.session_handler = session_handler

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:

        if scope["type"] not in ("http", "websocker"):
            await self.app(scope, receive, send)
            return

        connection = HTTPConnection(scope)
        session = HTTPSession(
            connection,
            handler=self.session_handler,
            session_name=self.session_name,
            gc_lifetime=self.gc_lifetime,
        )
        scope["session"] = session

        async def send_wrap(message: Message):

            if message["type"] == "http.response.start":
                if scope["session"]:

                    session: HTTPSession = scope["session"]
                    header_value: str
                    if session.should_send_cookie():
                        headers = MutableHeaders(scope=message)
                        
                        if session.is_destoried():
                            header_value = (
                                "%s=%s; path=%s;Max-Age=-1;"
                                % (
                                    self.session_name,
                                    session.session_id,
                                    self.cookie_path
                                )
                            )
                        else:
                            header_value = "%s=%s; path=%s;" % (
                                self.session_name,
                                session.session_id,
                                self.cookie_path
                            )

                            if self.cookie_expire > 0:
                                header_value += "Max-Age=%d;" % (
                                    self.cookie_expire
                                )
                            elif self.cookie_expire < 0:
                                header_value += "Max-Age=%d;" % (
                                    self.cookie_expire
                                )

                        if self.cookie_samesite:
                            header_value += "SameSite=%s;" % (self.cookie_samesite)

                        if self.cookie_domain:
                            header_value += "Domain=%s;" % (self.cookie_domain)

                        if self.cookie_samesite:
                            header_value += "SameSite=%s;" % (self.cookie_samesite)

                        if self.cookie_httponly:
                            header_value += "HttpOnly;"
                        
                        if self.cookie_secure and connection.headers.get("https"):
                            header_value += "Secure"

                        headers.append("Set-Cookie", header_value)

                    session.close()
            await send(message)

        await self.app(scope, receive, send_wrap)
