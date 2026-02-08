from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.types import ASGIApp, Receive, Scope, Send
from typing import Callable
from app.db import async_session


class DBSessionMiddleware(BaseHTTPMiddleware):
    """
    Attaches an AsyncSession to `request.state.db` for each incoming request.
    Handlers may use `request.state.db` if they prefer middleware-provided sessions.
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable):
        async with async_session() as session:
            request.state.db = session
            response = await call_next(request)
            return response

