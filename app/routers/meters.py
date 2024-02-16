from typing import Union, Dict, List
import bson.errors
import pymongo.errors
from fastapi import APIRouter, Depends, HTTPException, Request, Body
from app.models.meters import Meter, MeterRes, MeterUpdate
from app.models.common import PyObjectId
from fastapi.encoders import jsonable_encoder

# from ..dependencies import get_token_header

router = APIRouter(
    prefix="/meters",
    tags=["smart meters"],
    # dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)


# endpoint for register new smart meter
@router.post("/meter", response_model=List[MeterRes], response_model_by_alias=False)
def register_smart_meter(request: Request, meter: Meter = Body(...), ):
    try:
        meter_dict = jsonable_encoder(meter)
        new_meter = request.app.db["meters"].insert_one(meter_dict)
        # registered_meter = request.app.db["meters"].find_one({"_id": new_meter.inserted_id})
        all_meters = request.app.db["meters"].find()
        return list(all_meters)
    except pymongo.errors.DuplicateKeyError:
        raise HTTPException(status_code=400, detail='Device id already exists')


# endpoint for listing all smart meters
@router.get("", response_model=List[MeterRes], response_model_by_alias=False)
def get_meters(request: Request):
    try:
        smart_meters = request.app.db["meters"].find()
        return list(smart_meters)
    except pymongo.errors.PyMongoError:
        raise HTTPException(status_code=500, detail='error fetching smart meters')


# endpoint for returning specific smart meter
@router.get("/{meter_id}", response_model=Union[MeterRes, None], response_model_by_alias=False)
def get_meter_by_id(request: Request, meter_id: str):
    try:
        mid = PyObjectId(meter_id)
        smart_meter = request.app.db["meters"].find_one({"_id": mid})
        return smart_meter
    except bson.errors.InvalidId:
        raise HTTPException(status_code=400, detail='Invalid ID')
    except pymongo.errors.PyMongoError:
        raise HTTPException(status_code=500)


# endpoint for updating smart meter details
@router.put("/{meter_id}", response_model=List[MeterRes], response_model_by_alias=False)
def update_smart_meter(request: Request, meter_id: str, meter: MeterUpdate = Body(...)):
    try:
        mid = PyObjectId(meter_id)
        updated_meter_dict = meter.to_dict()
        update_result = request.app.db["meters"].update_one({"_id": mid}, {"$set": updated_meter_dict})
        if update_result.modified_count == 1 or update_result.matched_count == 1:
            all_meters = request.app.db["meters"].find()
            return list(all_meters)
        else:
            raise HTTPException(status_code=400, detail='Smart meter not found')
    except bson.errors.InvalidId:
        raise HTTPException(status_code=400, detail='Invalid ID')


# endpoint to delete smart meter
@router.delete("/{meter_id}", response_model=List[MeterRes], response_model_by_alias=False)
def delete_meter(request: Request, meter_id: str):
    try:
        mid = PyObjectId(meter_id)
        # delete selected smart meter
        res = request.app.db["meters"].delete_one({"_id": mid})
        # Return all meters after deletion
        if res.deleted_count == 0:
            raise HTTPException(status_code=400, detail='Smart meter not found.')
        all_meters = list(request.app.db["meters"].find())
        return all_meters
    except bson.errors.InvalidId:
        raise HTTPException(status_code=400, detail='Invalid ID')
    except pymongo.errors.PyMongoError:
        raise HTTPException(status_code=500)
