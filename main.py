from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi.middleware.cors import CORSMiddleware
from routes.accounts_route import router as account_auth
from routes.refresh_token import router as refresh_router
from routes.profile_route import router as account_profile
from routes.teacher_class_route import router as teacher_classes
from routes.teacher_module_route import router as teacher_modules
from routes.teacher_assessment_route import router as teacher_assessments
from routes.student_module_route import activities_router as student_activities
from routes.student_module_route import router as student_modules
from routes.handsign_route import router as handsign_router
from core.handsign_config import get_handsign_settings
from services.handsign.prediction_service import PredictionService
from limiter import limiter

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")


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
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5177",
    "http://127.0.0.1:5177",
] 

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"]
)

def cors_headers(request: Request):
    origin = request.headers.get("origin")
    if origin not in origins:
        return {}

    return {
        "Access-Control-Allow-Origin": origin,
        "Vary": "Origin",
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Headers": "Authorization, Content-Type",
        "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS",
    }

@app.options("/{full_path:path}")
async def preflight_handler(request: Request, full_path: str):
    return JSONResponse(status_code=200, content={}, headers=cors_headers(request))

@app.exception_handler(HTTPException)
async def http_exception_with_cors(request: Request, exc: HTTPException):
    response = JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )
    for key, value in cors_headers(request).items():
        response.headers[key] = value
    return response

app.include_router(account_auth)
app.include_router(account_profile)
app.include_router(refresh_router)
app.include_router(teacher_classes)
app.include_router(teacher_modules)
app.include_router(teacher_assessments)
app.include_router(student_modules)
app.include_router(student_activities)
app.include_router(handsign_router)

@app.on_event("startup")
def load_handsign_model():
    app.state.handsign_prediction_service = PredictionService(get_handsign_settings())

@app.on_event("shutdown")
def close_handsign_model():
    service = getattr(app.state, "handsign_prediction_service", None)
    if service is not None:
        service.close()

@app.get("/")
def root():
    return{"message": "FastAPI running on Port 8000..."}
