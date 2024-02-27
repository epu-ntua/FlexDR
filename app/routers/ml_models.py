from typing import List, Union, Dict
import pymongo
from fastapi import APIRouter, Request, HTTPException, Body, Depends
import bson
from fastapi.encoders import jsonable_encoder
from app.models.ml_models import MLModel, MLModelRes
from app.models.common import PyObjectId
from app.auth.auth import has_access_to_admin_routes
# from ..dependencies import get_token_header

router = APIRouter(
    prefix="/models",
    tags=["ml_models"],
    dependencies=[Depends(has_access_to_admin_routes)],
    responses={404: {"description": "Not found"}},
)


# endpoint for register new ml model
@router.post("/model", response_model=MLModelRes, response_model_by_alias=False)
def register_ml_model(request: Request, ml_model: MLModel = Body(...), ):
    try:
        ml_model_dict = jsonable_encoder(ml_model)
        new_ml_model = request.app.db["ml_models"].insert_one(ml_model_dict)
        registered_ml_model = request.app.db["ml_models"].find_one({"_id": new_ml_model.inserted_id})
        return registered_ml_model
    except pymongo.errors.DuplicateKeyError:
        raise HTTPException(status_code=400, detail='Model uri already exists')


# endpoint for returning all ML models
@router.get("", response_model=List[MLModelRes], response_model_by_alias=False)
def get_ml_models(request: Request):
    try:
        ml_models = request.app.db["ml_models"].find()
        return list(ml_models)
    except Exception as e:
        raise HTTPException(status_code=500, detail='error fetching ML models')


# endpoint for returning specific ML model
@router.get("/{ml_model_id}", response_model=Union[MLModelRes, None], response_model_by_alias=False)
def get_ml_model(request: Request, ml_model_id: str):
    try:
        mid = PyObjectId(ml_model_id)
        ml_model = request.app.db["ml_models"].find_one({"_id": mid})
        return ml_model
    except bson.errors.InvalidId:
        raise HTTPException(status_code=400, detail='Invalid ID')
    except pymongo.errors.PyMongoError:
        raise HTTPException(status_code=500)


@router.get("/prod/model", response_model=Dict[str,str], response_model_by_alias=False)
def get_prod_model(request: Request):
    try:
        ml_models = request.app.db['ml_models'].find({"production": "True"})
        ml_models_list = list(ml_models)
        if len(ml_models_list) != 1:
            raise HTTPException(status_code=500)
        prod_mid = ml_models_list[0].get('_id', None)
        return {'id': str(prod_mid)}
    except pymongo.errors.PyMongoError:
        raise HTTPException(status_code=500)
