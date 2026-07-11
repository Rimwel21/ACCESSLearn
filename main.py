from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi.middleware.cors import CORSMiddleware
from routes.accounts_route import router as account_auth
from routes.refresh_token import router as refresh_router
from routes.profile_route import router as account_profile
from routes.admin_route import router as admin_router
from routes.teacher_route import router as teacher_router
from limiter import limiter

app = FastAPI()


app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

@app.exception_handler(RateLimitExceeded)
async def custom_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Too many requests. Please try again later."
        }
    )

origins = [
    "http://localhost:5173/"
] 

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # babaguhin koto kapag may frontend na
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(account_auth)
app.include_router(account_profile)
app.include_router(refresh_router)
app.include_router(admin_router)
app.include_router(teacher_router)

@app.get("/")
def root():
    return{"message": "FastAPI running on Port 8000..."}