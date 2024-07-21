#!/usr/bin/env python3


from fastapi import FastAPI, HTTPException
from starlette.requests import Request, ClientDisconnect
from starlette.responses import StreamingResponse
from starlette.background import BackgroundTask
import httpx


api = FastAPI()
last_domain = ''


async def _reverse_proxy(request: Request):
    global last_url
    # TODO: If no domain on path, auto use last_url
    # TODO: Auto-remap both absolute, and relative link(s) to proxied one from responses.

    # Construct the base URL dynamically based on the path parameter
    path = request.url.path
    domain = path.split('/')[1]
    path = path.lstrip('/').replace(domain, '').lstrip('/')
    query = request.url.query

    try:
        client = httpx.AsyncClient(base_url=f"https://{domain}/{path}/")

        if query:
            url = httpx.URL(scheme="https",
                            host=domain,
                            path=path,
                            query=request.url.query.encode("utf-8"))
        else:
            url = httpx.URL(scheme="https",
                            host=domain,
                            path=path)

        headers = dict(request.headers)
        headers['host'] = domain  # Set the 'host' header based on the path parameter
        rp_req = client.build_request(request.method, url,
                                    headers=headers,
                                    content=request.stream())
        rp_resp = await client.send(rp_req, stream=True)

        resp_headers = dict(rp_resp.headers)
        resp_headers['x-frame-options'] = "Allow"

        del client
    except ClientDisconnect:
        return
    except Exception as e:
        raise HTTPException(detail=str(e),
                            status_code=500)

    return StreamingResponse(
        rp_resp.aiter_raw(),
        status_code=rp_resp.status_code,
        headers=resp_headers,
        background=BackgroundTask(rp_resp.aclose),
    )


# Route definition now includes the path parameter
api.add_route("/{path:path}",
              _reverse_proxy, ["TRACE", "GET", "HEAD", "POST", "PUT", "PATCH", "DELETE"])


if __name__ == '__main__':
    import uvicorn
    uvicorn.run('main:api', host='0.0.0.0', port=2580, reload=True)