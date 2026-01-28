from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from starlette.middleware.cors import CORSMiddleware
from routers import auth_router, requests, websocket_manager
from config import settings

app = FastAPI(title="License Management App")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Templates
templates = Jinja2Templates(directory="templates")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    from sqlalchemy import text
    from database import engine
    with engine.connect() as conn:
        conn.execution_options(isolation_level="AUTOCOMMIT")
        try:
            conn.execute(text("ALTER TABLE license_requests ADD COLUMN IF NOT EXISTS license_verified BOOLEAN DEFAULT FALSE;"))
            conn.execute(text("ALTER TABLE license_requests ADD COLUMN IF NOT EXISTS license_verified_at TIMESTAMP NULL;"))
            conn.execute(text("ALTER TABLE license_requests ADD COLUMN IF NOT EXISTS license_rejected BOOLEAN DEFAULT FALSE;"))
            conn.execute(text("ALTER TABLE license_requests ADD COLUMN IF NOT EXISTS license_rejected_at TIMESTAMP NULL;"))
            conn.execute(text("ALTER TABLE license_requests ADD COLUMN IF NOT EXISTS license_key VARCHAR NULL;"))
            print("Schema migration completed on startup.")
        except Exception as e:
            print(f"Startup migration error (ignorable): {e}")

# Routers
app.include_router(auth_router.router)
app.include_router(requests.router)

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/dashboard")
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket_manager.manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # We don't really expect messages from client for now, mostly broadcasting
            pass
    except WebSocketDisconnect:
        websocket_manager.manager.disconnect(websocket)
