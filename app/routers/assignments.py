import datetime
from typing import Union, Dict, List
import bson.errors
import pymongo.errors
from fastapi import APIRouter, Depends, HTTPException, Request, Body
from app.models.common import PyObjectId
from app.models.assignments import Assignment, AssignmentRes, AssignmentDetailedRes, AssignmentUpdate
from fastapi.encoders import jsonable_encoder
from app.auth.auth import has_access_to_admin_routes, has_access_to_prosumer_routes, get_userinfo

# from ..dependencies import get_token_header

router = APIRouter(
    prefix="/assignments",
    tags=["assignments"],
    # dependencies=[Depends(has_access_to_admin_routes)],
    responses={404: {"description": "Not found"}},
)

'''
This endpoint implements the creation of an assignment.
The clustering service will create in daily basis an prediction for each smart meter.
This prediction will be done by the model deployed in production the current date.
'''


@router.post("/assignment", response_model=AssignmentDetailedRes, response_model_by_alias=False)
def create_assignment(request: Request, assignment: Assignment = Body(...), ):
    try:
        # ml model id
        mid = PyObjectId(assignment.ml_model_id)
        # smart meter id
        smid = assignment.meter_id
        # get meter
        meter = request.app.db["meters"].find_one({"device_id": smid})
        if meter is None:
            raise HTTPException(status_code=400, detail='Specific smart meter does not exist')
        # find cluster profile for specific model containing the assigned cluster
        pipeline = [
            {
                "$match": {
                    "ml_model_id": mid,  # cluster profile with specific model id
                    "clusters.number": assignment.cluster_assigned  # cluster assigned exist in cl. profile clusters
                }
            },
            {
                "$lookup": {
                    "from": "ml_models",
                    "localField": "ml_model_id",
                    "foreignField": "_id",
                    "as": "ml_model"
                }
            },
            {
                "$unwind": "$ml_model"  # Unwind the 'ml_model_info' array (optional)
            },
            {
                "$addFields": {
                    "cluster": {
                        "$filter": {
                            "input": "$ml_model.clusters",
                            "as": "cluster",
                            "cond": {"$eq": ["$$cluster.number", assignment.cluster_assigned]}
                        }
                    }
                }
            },
            {
                "$project": {
                    "ml_model.clusters": 0,
                    "ml_model_id": 0,
                    # "meter_id": 0,
                }
            }
        ]
        results = list(request.app.db["cluster_profiles"].aggregate(pipeline))
        if len(results) > 1:
            raise HTTPException(status_code=409,
                                detail='More than one profiles found. Please check configuration of cluster profiles.')
        elif len(results) == 0:
            raise HTTPException(status_code=409,
                                detail='Assigned cluster does not exist in any cluster profiles')

        cluster_profile = results[0]
        ml_model = cluster_profile.pop("ml_model")
        # construct assignment
        forecast_date = assignment.forecast_date
        parsed_forecast_date = datetime.datetime.strptime(forecast_date, "%Y-%m-%d")
        forecast_datetime = parsed_forecast_date.replace(hour=0, minute=0, second=0, microsecond=0,
                                                         tzinfo=datetime.timezone.utc)
        assignment_dict = {
            "meter": meter,
            "ml_model": ml_model,
            "assigned_cluster_profile": cluster_profile,
            "assigned_cluster": assignment.cluster_assigned,
            "creation_datetime": datetime.datetime.now(tz=datetime.timezone.utc),
            "forecast_datetime": forecast_datetime,
            "forecasted_load": assignment.forecasted_load
        }
        inserted_assignment = request.app.db["assignments"].insert_one(assignment_dict)
        created_assignment = request.app.db["assignments"].find_one({"_id": inserted_assignment.inserted_id})
        return created_assignment
    except bson.errors.InvalidId:
        raise HTTPException(status_code=400, detail='Invalid ID')


@router.get("/daily", response_model=List[AssignmentDetailedRes],
            response_model_by_alias=False)
def get_daily_assignment(request: Request, valid: bool = Depends(has_access_to_prosumer_routes),
                         userinfo=Depends(get_userinfo)):
    try:
        device_id = userinfo.get('smart_meter_id')
        ml_models = request.app.db['ml_models'].find({"production": "True"})
        ml_models_list = list(ml_models)
        if len(ml_models_list) != 1:
            raise HTTPException(status_code=500)
        ml_model_id = ml_models_list[0].get('_id')

        current_date = datetime.datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        # Construct the query for current date
        query = {
            "ml_model._id": ml_model_id,
            "meter.device_id": device_id,
            "forecast_datetime": {
                "$gte": current_date,
                "$lt": current_date + datetime.timedelta(days=2)
            }
        }
        results = request.app.db["assignments"].find(query)
        assignments = list(results)
        if len(assignments) > 2:
            raise HTTPException(status_code=409, detail='More than two day ahead assignments for this meter.')

        return [] if len(assignments) == 0 else assignments
    except bson.errors.InvalidId:
        raise HTTPException(status_code=400, detail='Invalid ID')
    except pymongo.errors.PyMongoError:
        raise HTTPException(status_code=500)


@router.get("", response_model=List[AssignmentDetailedRes],
            response_model_by_alias=False)
def get_all_assignments(request: Request, valid: bool = Depends(has_access_to_admin_routes)):
    try:
        results = request.app.db["assignments"].find()
        assignments = list(results)
        return assignments
    except pymongo.errors.PyMongoError:
        raise HTTPException(status_code=500)


@router.put("/edit/{assignment_id}", response_model=AssignmentDetailedRes, response_model_by_alias=False)
def edit_assignment(request: Request, assignment_id, assignment: AssignmentUpdate = Body(...),
                    valid: bool = Depends(has_access_to_admin_routes)):
    try:
        asid = PyObjectId(assignment_id)
        recommendation = assignment.recommendation
        updated_recommendation_dict = recommendation.dict()
        update_result = request.app.db["assignments"].update_one({"_id": asid}, {"$set": {
            "assigned_cluster_profile.recommendation": updated_recommendation_dict
        }})
        if update_result.modified_count == 1 or update_result.matched_count == 1:
            updated_assignment = request.app.db["assignments"].find_one({"_id": asid})
            return updated_assignment
        else:
            raise HTTPException(status_code=400, detail='Assignment not found')
    except bson.errors.InvalidId:
        raise HTTPException(status_code=400, detail='Invalid ID')


@router.get("/meter/{meter_id}", response_model=List[AssignmentDetailedRes],
            response_model_by_alias=False)
def get_meter_assignments(request: Request, meter_id: str, valid: bool = Depends(has_access_to_admin_routes)):
    try:
        meter_id = PyObjectId(meter_id)
        ml_models = request.app.db['ml_models'].find({"production": "True"})
        ml_models_list = list(ml_models)
        if len(ml_models_list) != 1:
            raise HTTPException(status_code=500)
        ml_model_id = ml_models_list[0].get('_id')

        current_date = datetime.datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        # Construct the query for current date
        query = {
            "ml_model._id": ml_model_id,
            "meter._id": meter_id,
            "forecast_datetime": {
                "$gte": current_date,
                "$lt": current_date + datetime.timedelta(days=2)
            }
        }
        results = request.app.db["assignments"].find(query)
        assignments = list(results)
        if len(assignments) > 2:
            raise HTTPException(status_code=409, detail='More than two day ahead assignments for this meter.')

        return [] if len(assignments) == 0 else assignments
    except bson.errors.InvalidId:
        raise HTTPException(status_code=400, detail='Invalid ID')
    except pymongo.errors.PyMongoError:
        raise HTTPException(status_code=500)


@router.get("/{meter_id}/{ml_model_id}", response_model=Union[AssignmentDetailedRes, None],
            response_model_by_alias=False)
def get_day_ahead_assignments(request: Request, meter_id: str, ml_model_id: str, valid: bool = Depends(has_access_to_admin_routes)):
    try:
        meter_id = PyObjectId(meter_id)
        ml_model_id = PyObjectId(ml_model_id)

        current_date = datetime.datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        # Construct the query for current date
        query = {
            "ml_model._id": ml_model_id,
            "meter._id": meter_id,
            "forecast_datetime": {
                "$gte": current_date + datetime.timedelta(days=1),
                "$lt": current_date + datetime.timedelta(days=2)
            }
        }
        results = request.app.db["assignments"].find(query)
        assignments = list(results)
        if len(assignments) > 1:
            raise HTTPException(status_code=409, detail='More than one day ahead assignments for this meter.')

        return None if len(assignments) == 0 else assignments[0]
    except bson.errors.InvalidId:
        raise HTTPException(status_code=400, detail='Invalid ID')
    except pymongo.errors.PyMongoError:
        raise HTTPException(status_code=500)


@router.get("/{assignment_id}", response_model=Union[AssignmentDetailedRes, None], response_model_by_alias=False)
def get_assignment_by_id(request: Request, assignment_id: str, valid: bool = Depends(has_access_to_admin_routes)):
    try:
        asid = PyObjectId(assignment_id)
        assignment = request.app.db["assignments"].find_one({"_id": asid})
        return assignment
    except bson.errors.InvalidId:
        raise HTTPException(status_code=400, detail='Invalid ID')
    except pymongo.errors.PyMongoError:
        raise HTTPException(status_code=500)
