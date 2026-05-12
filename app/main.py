from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.db.session import Base, engine
from app.routers.internal import router as internal_router
from app.routers.push import router as push_router

app = FastAPI(title="Ali Supplier Register API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_origin_regex=r".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"ok": True}


app.include_router(push_router)
app.include_router(internal_router)

# 静态文件放最后，避免覆盖API路由
app.mount("/", StaticFiles(directory="static", html=True), name="static")
