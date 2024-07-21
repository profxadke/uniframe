#!/usr/bin/env python3


from typing import Optional
from urllib.parse import urlencode
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, RedirectResponse
from starlette.background import BackgroundTask
from urllib.parse import urlparse
import httpx


app = FastAPI()


# Initialize HTTPX AsyncClient
client = httpx.AsyncClient()


def parse_domain(path):
    return urlparse(path).netloc.split(":")[0]


@app.middleware("http")
async def reverse_proxy(request: Request, call_next):
    # Extract domain and path from query parameters
    domain = request.query_params.get("domain")
    path = request.query_params.get("path", "")

    if not domain:
        raise HTTPException(status_code=400, detail="Domain parameter is required")

    # Construct the base URL dynamically
    BASE_URL = f"https://{domain}/{path}"

    print(domain, path)
    proxy_request_url = request.url_for("proxy", domain=domain, path=path)
    query_params = urlencode(request.query_params.items())
    proxy_request_full_url = f"{BASE_URL}{proxy_request_url}?{query_params}"

    headers = dict(request.headers)
    headers["host"] = domain  # Set the 'host' header based on the incoming request's domain

    proxy_request = httpx.Request(
        method=request.method,
        url=proxy_request_full_url,
        headers=headers,
        data=await request.body(),
    )
    
    async with client.stream(proxy_request) as response:
        return StreamingResponse(
            response.aiter_raw(),
            status_code=response.status_code,
            headers=dict(response.headers),
            background=BackgroundTask(response.aclose),
        )


@app.get('/')
async def redirect_docs():
    RedirectResponse('/docs')


@app.get("/proxy")
async def proxy(
    request: Request,
    domain: str,
    path: Optional[str] = ""
):
    return await reverse_proxy(request, parse_domain(path), path)


'''
@app.get("/{path:path}")
async def proxy(
    request: Request,
    path: str
):
    return RedirectResponse(f"/proxy?domain={parse_domain(path)}&path={path}")
'''


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=2580)