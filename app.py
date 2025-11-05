import os
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from config import Config
from routes.admin_routes import admin_router
from routes.credit_routes import credit_router
from routes.user_routes import user_router
from routes.auth_routes import auth_router
from routes.website_routes import website_router
from routes.data_routes import data_router
from routes import leaderboard_routes

ADMIN_PATH = os.getenv("ADMIN_PORTAL") or "/admin"

# initialize FastAPI app
app = FastAPI(title="Taqneeq Backend API")

# enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# register routers
app.include_router(website_router, prefix=ADMIN_PATH, tags=["website"])
app.include_router(admin_router, prefix="/admin", tags=["admin"])
app.include_router(credit_router, tags=["credits"])
app.include_router(user_router, prefix="/user", tags=["users"])
app.include_router(auth_router, tags=["auth"])
app.include_router(data_router, tags=["data"])
app.include_router(leaderboard_routes.router)

@app.get('/')
async def home():
    return RedirectResponse(url="https://taqneeqfest.com/")

@app.get('/favicon.ico')
@app.get('/robots.txt')
@app.get('/sitemap.xml')
@app.get('/security.txt')
async def static_from_root(request: Request):
    filename = request.url.path[1:]
    return FileResponse(f"static/{filename}")

if __name__ == '__main__':
    import uvicorn
    port = int(os.getenv('PORT', 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)