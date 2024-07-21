#!/usr/bin/env python3


from typing import Optional
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse
from starlette.background import BackgroundTask
import httpx


app = FastAPI()


# Initialize HTTPX AsyncClient
client = httpx.AsyncClient()


async def reverse_proxy(request: Request, domain: str, path: Optional[str] = None):
    # Construct the base URL dynamically based on domain and path
    base_url = f"https://{domain}"
    if path:
        base_url += f"/{path}"

    # Construct the full URL for the proxy request
    proxy_url = base_url + request.url.query

    # Forward headers from the original request
    headers = dict(request.headers)
    headers["host"] = domain  # Set the 'host' header based on the incoming request's domain

    url = proxy_url

    # Create a proxy request with httpx
    proxy_request = httpx.Request(
        method=request.method,
        url=url,
        headers=headers,
        content=await request.body(),
    )

    proxy_request.url = proxy_url

    # Send the proxy request and stream the response back
    async with client.stream(proxy_request, url=url) as response:
        # print('R1', response)
        return StreamingResponse(
            response.aiter_raw(),
            status_code=response.status_code,
            headers=dict(response.headers),
            background=BackgroundTask(response.aclose),
        )


@app.route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD", "TRACE"])
async def proxy_handler(request: Request):
    # TODO: De-schemize URL / path parameter (remove http/https and ://)
    path = request.url.path
    domain = path.split('/')[1]
    path = path.lstrip('/').replace(domain, '').lstrip('/')
    return await reverse_proxy(request, domain, path)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=2580)