from typing import Optional
from fastapi.datastructures import Default
from fastapi.params import Query
from fastapi.testclient import TestClient
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette_session import HTTPSession, SessionMiddleware, RedisSessionHandler

SESSION_NAME = "PYSESSIONID"


async def set_session(request: Request):
    data = await request.json()
    session: HTTPSession = request.session
    session.start(True)
    session.set("test", data)
    return JSONResponse({"session_id": session.session_id})


async def get_session(request: Request):
    session: HTTPSession = request.session
    session.start(False)
    data = session.get("test")

    return JSONResponse({"session": data})


async def destory_session(request: Request):
    session: HTTPSession = request.session    
    session.destory()
    return JSONResponse({"session": "deleted"})


async def regenerate_session_id(request: Request):
    session: HTTPSession = request.session
    session.start(False)
    session.regenerate_session_id(True)    
    return JSONResponse({"session_id": session.session_id})


def create_app():
    app = FastAPI()
    app.add_route("/session/set", set_session, methods=["POST"])
    app.add_route("/session/get", get_session)
    app.add_route("/session/regenerate_session_id", regenerate_session_id, methods=["POST"])
    app.add_route("/session/destory", destory_session)
    session_handler = RedisSessionHandler(host="localhost", port=6379)
    app.add_middleware(
        SessionMiddleware, session_handler=session_handler, session_name=SESSION_NAME
    )

    return app


def test_session():

    app = create_app()

    test_client = TestClient(app)
    test_data = {"test": "testest"}

    response = test_client.post("/session/set", json=test_data)
    response_json = response.json()
    session_id = response.cookies.get(SESSION_NAME)
    print(f"session id={session_id}")
    assert session_id == response_json.get("session_id"), session_id

    test_client = TestClient(app)
    test_client.cookies.set(SESSION_NAME, session_id)
    response = test_client.get("/session/get")
    response_json = response.json()
    assert response_json.get("session") == test_data

    
    test_client = TestClient(app)
    test_client.cookies.set(SESSION_NAME, session_id)
    response=test_client.get("/session/destory")

    test_client = TestClient(app)
    test_client.cookies.set(SESSION_NAME, session_id)
    response = test_client.get("/session/get?create=False")
    response_json = response.json()
    assert response_json.get("session") == test_data

    test_client = TestClient(app)
    test_client.cookies.set(SESSION_NAME, session_id)
    response=test_client.get("/session/destory")

    assert True
    

def test_regenerate_session_id():

    app = create_app()
 
    test_client = TestClient(app)
    test_data = {"test": "testest"}

    response = test_client.post("/session/set", json=test_data)
    response_json = response.json()
    session_id = response.cookies.get(SESSION_NAME)    
    assert session_id == response_json.get("session_id"), session_id

    print(f"old session id {session_id}")

    response = test_client.post("/session/regenerate_session_id", json=test_data)
    response_json = response.json()

    print(response_json)
    new_session_id = response.cookies.get(SESSION_NAME)    
    assert new_session_id is not None
    assert new_session_id == response_json.get("session_id"), new_session_id
    assert new_session_id != session_id

    test_client.cookies.set(SESSION_NAME, new_session_id)
    response = test_client.get("/session/get")
    response_json = response.json()
    assert response_json.get("session") == test_data

    print(f"new session id {new_session_id}")
    test_client.cookies.set(SESSION_NAME, new_session_id)
    response=test_client.get("/session/destory")
    assert True