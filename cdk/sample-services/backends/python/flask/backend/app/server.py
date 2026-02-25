from flask import Flask
import os

app = Flask(__name__)

environment = os.getenv("ENVIRONMENT") 

if environment == None:
    environment = "development"

@app.route("/")
def root():
     print('/')
     print(environment)
     return {"message": "Hello World - Backend API" + environment}

@app.route("/api")
def api():
     print("/api")
     return {"message": "Hello World - Backend API - " + environment}

# Healthcheck endpoint (could be the base API as well, but dedicated healthcheck is good to have)
@app.route("/api/health")
async def healthcheck():
    print("health")
    return {"message": "Healthy"}

if __name__ == '__main__':
     app.run(host='0.0.0.0', port=8000)