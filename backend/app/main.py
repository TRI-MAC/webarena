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
    os.getenv("APP_SERVICES_FRONTEND_SERVICE_URL"),
    os.getenv("APP_SERVICES_BACKEND_SERVICE_URL"),
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
    return {"message": "Hello World - Backend API - " + environment}

# Healthcheck endpoint (could be the base API as well, but dedicated healthcheck is good to have)
@router.get("/health")
async def healthcheck():
    return {"message": "Healthy"}

@router.get("/v0/test_s3")
async def test_s3():
    s3 = boto3.resource('s3')
    s3_bucket_resolved_name = os.getenv("AWS_SERVICES_S3_DATA_BUCKET_RESOLVED_NAME")
    data_bucket = s3.Bucket(s3_bucket_resolved_name)
    number_objects_in_bucket = 0

    for i in data_bucket.objects.all():
        number_objects_in_bucket = number_objects_in_bucket + 1

    return {"message": "s3 Test Connection: The bucket " + s3_bucket_resolved_name + " contains " + str(number_objects_in_bucket) + " objects"}

@router.get("/v0/test_dynamodb")
async def test_s3():
    dynamodb = boto3.resource('dynamodb')
    dynamodb_table_name = os.getenv("AWS_SERVICES_DYNAMODB_TABLE_NAME")
    table = dynamodb.Table(dynamodb_table_name)
    return {"message": "Table" + dynamodb_table_name + " is accessible and created on: " + str(table.creation_date_time)}

app.include_router(router)