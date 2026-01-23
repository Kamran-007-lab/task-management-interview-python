import os
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

load_dotenv()

from models import init_db
from config.redis import init_redis
from jobs.email_job import init_job_queue
from routes.auth import router as auth_router
from routes.tasks import router as tasks_router

app = FastAPI()

PORT = int(os.getenv('PORT', 8000))

@app.middleware("http")
async def add_body_parser(request: Request, call_next):
    response = await call_next(request)
    return response

app.include_router(auth_router, prefix='/api/auth')
app.include_router(tasks_router, prefix='/api/tasks')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:8000', 'http://localhost:8001'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)

@app.get('/health')
async def health_check():
    return {'status': 'OK', 'timestamp': datetime.now().isoformat()}

# Error handling middleware
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f'Error: {exc}')
    return JSONResponse(
        status_code=500,
        content={'error': 'Something went wrong!'}
    )

# 404 handler
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={'error': 'Route not found'}
    )

# Startup event
@app.on_event('startup')
async def startup_event():
    try:
        # Initialize Redis
        init_redis()
        print('Redis connected successfully')

        # Initialize job queue
        await init_job_queue()
        print('Job queue initialized')

        # Sync database
        init_db()
        print('Database synchronized')

        print(f'Server running on port {PORT}')
        print(f'Environment: {os.getenv("NODE_ENV")}')
    except Exception as error:
        print(f'Failed to start server: {error}')
        raise

# Shutdown event
@app.on_event('shutdown')
async def shutdown_event():
    print('Server shutting down')

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=PORT)
