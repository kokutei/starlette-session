# starlette-session

starlette-session is an middleware for FastAPI that support server-side session to your application. 
A unique session ID is stored in a cookie on the user side.

# Install

I'm Sorry, this is my first python program. I have no plans to upload it to PyPI.
Please download from here and install.

``` bash
$ git clone https://github.com/kokutei/starlette-session.git
$ cd starlette-session
$ python setup.py install --user
```

# Examples

## Start session and set/get data from session

```python main.py

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette_session import HTTPSession, SessionMiddleware, RedisSessionHandler

app = FastAPI()

session_handler = RedisSessionHandler(host="localhost", port=6379)
app.add_middleware(
    SessionMiddleware, session_handler=session_handler, session_name=SESSION_NAME
)

@app.post("/session/set")
def set_session(request: Request):
    session: HTTPSession = request.session
    
    # Redis will be open when start() is called     
    session.start(True)
    data= "testdata"
    session.set("test", data)
    return { "session_data": data}


@app.get("/session/get")
def get_session(request: Request):
    session: HTTPSession = request.session

    # start(False), If no session id in cookie, will not be read session data from backend.
    session.start(False)    
    session.get("test")
    return { "session_data": data}
```

## Destory session data

Delete session data from backend storage.

```python 

@app.post("/session/destory")
def session_destory(request: Request):
    
    session: HTTPSession = request.session
    session.destory()

```

## Regenerate session id

```python

@app.post("/session/destory")
def session_destory(request: Request):
    
    session: HTTPSession = request.session
    session.start(False)
    
    # create new session id but don't delete old session data
    session.regenerate_session_id(False)
    
    # create new session id and delete old session data
    session.regenerate_session_id(True)
```
