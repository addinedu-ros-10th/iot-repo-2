from fastapi import FastAPI
from src.db.session import engine, Base
from src.api import user_router

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(user_router.router)

@app.get("/")
def read_root():
    return {"message": "안녕하세요! 공부 환경 자동화 시스템 API 서버입니다."}