from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
import requests

app = FastAPI(debug=True)

base_url = "https://www.google.com/"


@app.get("/titles/{path:path}")
async def read_root(request: Request, path: str):
    headers = {k: v for k, v in request.headers.items()}
    headers.pop('host')
    headers.pop('accept-encoding')

    res = requests.get(f'{base_url}{path}', params=request.query_params, headers=headers, stream=True)

    return StreamingResponse(
        res.iter_lines(),
        status_code=res.status_code,
        headers=headers,
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run('st:app', reload=True)