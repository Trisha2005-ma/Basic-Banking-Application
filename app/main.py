import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import JSONResponse, Response

from app import models  # noqa: F401  (registers the tables)
from app.api import accounts, auth
from app.core.exceptions import AppError
from app.db.base import Base
from app.db.session import engine

logger = logging.getLogger("bank")


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Basic Banking API",
    description="Register, log in, deposit, withdraw and transfer money.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None,
)


@app.get("/docs", include_in_schema=False)
async def swagger_ui():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - Swagger UI",
        swagger_css_url="/docs-theme.css",
    )


@app.get("/docs-theme.css", include_in_schema=False)
async def swagger_theme():
    return Response(
        content="""
html,
body {
    background: #f3f6f3;
}

.swagger-ui {
    color: #26342d;
    font-family: "Segoe UI Variable", "Segoe UI", sans-serif;
}

.swagger-ui .topbar {
    display: none;
}

.swagger-ui .wrapper {
    max-width: 1160px;
    padding: 0 32px;
}

.swagger-ui .info {
    margin: 36px 0 24px;
}

.swagger-ui .info .title {
    color: #164734;
    font-size: 32px;
    font-weight: 650;
}

.swagger-ui .info .title small {
    background: #e5efe8;
    border-radius: 3px;
    color: #276347;
    vertical-align: middle;
}

.swagger-ui .info .description p {
    color: #526158;
    font-size: 15px;
}

.swagger-ui .scheme-container {
    background: #fff;
    border: 1px solid #dce5dd;
    border-radius: 4px;
    box-shadow: none;
    margin: 0 0 28px;
    padding: 14px 20px;
}

.swagger-ui .btn.authorize {
    background: #247a52;
    border-color: #247a52;
    color: #fff;
}

.swagger-ui .btn.authorize:hover {
    background: #1b6241;
    border-color: #1b6241;
}

.swagger-ui .opblock-tag-section {
    margin-bottom: 24px;
}

.swagger-ui .opblock-tag {
    border-bottom: 1px solid #d5dfd7;
    color: #203a2c;
    font-size: 20px;
    padding: 12px 8px;
}

.swagger-ui .opblock {
    border-radius: 4px;
    box-shadow: none;
    margin: 0 0 10px;
    transition: box-shadow 120ms ease, transform 120ms ease;
}

.swagger-ui .opblock:hover {
    box-shadow: 0 3px 12px rgb(27 57 39 / 9%);
    transform: translateY(-1px);
}

.swagger-ui .opblock .opblock-summary {
    padding: 10px 14px;
}

.swagger-ui .opblock-summary-method {
    border-radius: 3px;
    min-width: 68px;
}

.swagger-ui .opblock-summary-path {
    overflow-wrap: anywhere;
}

.swagger-ui .opblock.opblock-get {
    background: #f0f7f2;
    border-color: #8eb99d;
}

.swagger-ui .opblock.opblock-get .opblock-summary-method {
    background: #26845c;
}

.swagger-ui .opblock.opblock-post {
    background: #fff8ed;
    border-color: #d9b474;
}

.swagger-ui .opblock.opblock-post .opblock-summary-method {
    background: #a85d17;
}

.swagger-ui .opblock.opblock-put {
    background: #eff5f8;
    border-color: #8aafc2;
}

.swagger-ui .opblock.opblock-put .opblock-summary-method {
    background: #3478a5;
}

.swagger-ui .opblock.opblock-delete {
    background: #fbf0ef;
    border-color: #d39a95;
}

.swagger-ui .opblock.opblock-delete .opblock-summary-method {
    background: #b64040;
}

.swagger-ui .opblock .opblock-body {
    background: #fff;
}

@media (max-width: 640px) {
    .swagger-ui .wrapper {
        padding: 0 16px;
    }

    .swagger-ui .info {
        margin-top: 24px;
    }

    .swagger-ui .info .title {
        font-size: 26px;
    }

    .swagger-ui .scheme-container {
        padding: 12px;
    }

    .swagger-ui .opblock .opblock-summary {
        padding: 9px;
    }
}
""",
        media_type="text/css",
    )


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    headers = {"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else None
    return JSONResponse(
        status_code=exc.status_code, content={"detail": exc.detail}, headers=headers
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error")  # full details only in the server log
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


app.include_router(auth.router)
app.include_router(accounts.router)
