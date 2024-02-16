import os
from contextlib import asynccontextmanager
import uvicorn
from pymongo.database import Database
from fastapi import FastAPI, Body, Depends, Request, HTTPException
from pymongo import MongoClient
from starlette.middleware.cors import CORSMiddleware
from app.routers import cluster_profiles, ml_models, meters, assignments

MONGO_USER = os.getenv('MONGO_USER')
MONGO_PASS = os.getenv('MONGO_PASS')
MONGO_HOST = os.getenv('MONGO_HOST')
MONGO_PORT = os.getenv('MONGO_PORT')


@asynccontextmanager
async def lifespan(app: FastAPI):
    mongo_client: MongoClient = MongoClient(f'mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:{MONGO_PORT}/')
    app.db: Database = mongo_client['flexibility']
    try:
        yield
    finally:
        print("Closing connection")
        mongo_client.close()


app = FastAPI(lifespan=lifespan)
app.include_router(cluster_profiles.router)
app.include_router(ml_models.router)
app.include_router(meters.router)
app.include_router(assignments.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Welcome to FlexDR"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
