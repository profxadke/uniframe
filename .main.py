from fastapi import FastAPI, HTTPException
from fastapi.middleware.base import BaseHTTPMiddleware
import httpx

app = FastAPI()

# Define the target server URL
TARGET_SERVER = "http://example.com"

# Endpoint mapping for reverse proxy
ENDPOINT_MAPPING = {
    "/api": "http://api.example.com",
    "/static": "http://static.example.com",
}

class ReverseProxyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # Check if the path matches an endpoint in the mapping
        for path, target_host in ENDPOINT_MAPPING.items():
            if request.url.path.startswith(path):
                # Forward the request to the target server
                target_url = f"{target_host}{request.url.path}"
                async with httpx.AsyncClient() as client:
                    response = await client.request(request.method, target_url, headers=dict(request.headers), data=await request.body())

                # Return the response to the client
                return response

        # If no matching endpoint found, proceed with the normal routing
        response = await call_next(request)
        return response

# Add reverse proxy middleware to the app
app.add_middleware(ReverseProxyMiddleware)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)