import asyncio
import os

import uvicorn

from app.api.rest import create_rest_app
from app.grpc.server import serve_grpc

TRANSPORT = os.getenv("TRANSPORT", "grpc")


async def main():

    tasks = []

    # REST is always running (for debugging or as a fallback)
    rest_app = create_rest_app()
    config = uvicorn.Config(rest_app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)
    tasks.append(server.serve())

    if TRANSPORT == "grpc":
        tasks.append(serve_grpc(port=50051))

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
