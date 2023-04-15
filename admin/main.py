import api
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()
app.mount('/static', StaticFiles(directory='dist'), name='dist')

app.include_router(api.router)


@app.route('/{path:path}')
async def index(request: Request):
    with open('./dist/index.html', 'r') as f:
        index = f.read()
    return HTMLResponse(index)


if __name__ == '__main__':
    uvicorn.run('main:app', host='0.0.0.0', port=6991, reload=True)
