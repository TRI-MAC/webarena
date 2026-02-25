from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
import boto3
import os

router = APIRouter(prefix='/api')

app = FastAPI()

environment = os.getenv("ENVIRONMENT") 

if environment == None:
    environment = "development"

origins = [
    os.getenv("FRONTEND_SERVICE_URL"),
    os.getenv("BACKEND_SERVICE_URL"),
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@router.get("/")
async def root():
    return {"message": "Hello World -FastAPI Backend API - " + environment}

# Healthcheck endpoint (could be the base API as well, but dedicated healthcheck is good to have)
@router.get("/health")
async def healthcheck():
    return {"message": "Healthy"}

app.include_router(router)