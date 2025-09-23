from fastapi import FastAPI
from database.database import engine, Base
from routers import users

# DB 테이블 생성을 위한 코드
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# FastAPI 앱 생성
app = FastAPI()

# FastAPI 앱이 시작될 때 create_tables 함수를 실행
@app.on_event("startup")
async def on_startup():
    await create_tables()

# users.py에 정의된 API들을 메인 앱에 포함
app.include_router(
    users.router,
    prefix="/users", # URL 경로 앞에 /users 를 붙여줌
    tags=["users"],   # API 문서에서 'users' 그룹으로 묶어줌
)

@app.get("/")
def read_root():
    return {"message": "Welcome to our API server!"}