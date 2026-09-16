from fastapi import FastAPI

from . import chat

app = FastAPI()

# The prefix matters: the frontend posts to /api/chat, and vite only proxies
# paths under /api (see frontend/vite.config.ts). The router itself declares
# just '/chat', so the two combine into /api/chat.
app.include_router(chat.router, prefix='/api')


@app.get('/')
async def root():
    return {'message': 'hello world'}
