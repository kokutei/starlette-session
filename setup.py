from setuptools import setup, find_packages

version = "0.1.0"
packages = ["sessions"]

setup(
    name="starlette-session", 
    version=version,
    description="server-side session middleware for FastAPI.",
    long_description="starlette-session is an middleware for FastAPI that support server-side session to your application.   ",
    author="kokutei.ri",
    license="MIT",
    classifiers=["Development Status :: 1 - Planning"],
    packages=["starlette_session", "starlette_session.handlers"],  
)
