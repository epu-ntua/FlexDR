from typing import Union, Dict, List
import bson
import pymongo.errors
from fastapi import APIRouter, Depends, HTTPException, Request, Body
from fastapi.encoders import jsonable_encoder
from app.models.common import PyObjectId
from app.models.cluster_profiles import ClusterProfile, ClusterProfileRes, ClusterProfileUpdate
from .dependencies import fetch_cluster_profiles


def find_matching(selected, all):
    matching_clusters = []
    for selected_cluster in selected:
        for cluster in all:
            if cluster['number'] == selected_cluster:
                matching_clusters.append(cluster)
                break
    return matching_clusters


# from ..dependencies import get_token_header

router = APIRouter(
    prefix="/cluster-profiles",
    tags=["cluster-profiles"],
    # dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)


@router.post("/profile", response_model=ClusterProfileRes, response_model_by_alias=False)
def create_cluster_profile(request: Request, profile: ClusterProfile = Body(...),
                           profiles: List = Depends(dependency=fetch_cluster_profiles)):
    try:
        mid = PyObjectId(profile.ml_model_id)
        for i, ex_prof in enumerate(profiles):
            clusters = [c["number"] for c in ex_prof["clusters"]]
            common = set(clusters).intersection(profile.selected_clusters)
            if len(common) > 0:
                raise HTTPException(status_code=400, detail='Selected clusters exist in other profile')
        # check if cluster exist in another cluster profile of the same ml model

        # check if model exist
        ml_model = request.app.db["ml_models"].find_one({"_id": mid})
        if ml_model is None:
            raise HTTPException(status_code=400, detail='Invalid Model')

        # check if selected clusters are valid
        matching_clusters = []
        for selected_cluster in profile.selected_clusters:
            for cluster in ml_model['clusters']:
                if cluster['number'] == selected_cluster:
                    matching_clusters.append(cluster)
                    break

        if len(matching_clusters) != len(profile.selected_clusters):
            raise HTTPException(status_code=400, detail='Invalid clusters selection')

        profile_dict = jsonable_encoder(profile)
        # REMOVE CLUSTERS, KEEP ONLY SELECTED
        # del ml_model['clusters']
        cluster_profile_dict = {
            # 'ml_model': {**ml_model},
            'ml_model_id': mid,
            'name': profile_dict.get("name"),
            'short_description': profile_dict.get("short_description"),
            'long_description': profile_dict.get("long_description"),
            'clusters': matching_clusters,
            'recommendation': {
                **profile_dict.get("recommendation")
            },
        }
        new_cluster_profile = request.app.db["cluster_profiles"].insert_one(cluster_profile_dict)
        # lookup pipeline
        pipeline = [
            {
                "$match": {"_id": new_cluster_profile.inserted_id}
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
                "$unwind": "$ml_model"
            },
            {
                "$project": {
                    "ml_model.clusters": 0,
                    "ml_model_id": 0,
                }
            }
        ]

        result = list(request.app.db["cluster_profiles"].aggregate(pipeline))
        return result[0]
        # created_cluster_profile = request.app.db["cluster_profiles"].find_one({"_id": new_cluster_profile.inserted_id})
    except bson.errors.InvalidId:
        raise HTTPException(status_code=400, detail='Invalid ID')


@router.get("/profile/{cluster_profile_id}", response_model=ClusterProfileRes, response_model_by_alias=False)
def get_cluster_profile(request: Request, cluster_profile_id: str):
    try:
        cpid = PyObjectId(cluster_profile_id)
        pipeline = [
            {
                "$match": {"_id": cpid}
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
                "$unwind": "$ml_model"
            },
            {
                "$project": {
                    "ml_model_id": 0,
                }
            }
        ]
        results = list(request.app.db["cluster_profiles"].aggregate(pipeline))
        if len(results) != 1:
            raise HTTPException(status_code=400, detail='Cluster profile not found')
        return results[0]
    except bson.errors.InvalidId:
        raise HTTPException(status_code=400, detail='Invalid ID')


@router.put("/profile/{cluster_profile_id}", response_model=ClusterProfileRes, response_model_by_alias=False)
def update_cluster_profile(request: Request, cluster_profile_id: str, profile: ClusterProfileUpdate = Body(...), ):
    try:
        cpid = PyObjectId(cluster_profile_id)
        profile_dict = profile.to_dict()

        pipeline = [
            {
                "$match": {"_id": cpid}
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
                "$unwind": "$ml_model"
            },
            {
                "$project": {
                    "ml_model_id": 0,
                }
            }
        ]
        results = list(request.app.db["cluster_profiles"].aggregate(pipeline))
        if len(results) != 1:
            raise HTTPException(status_code=400, detail='Cluster profile not found')
        current_profile = results[0]

        if "selected_clusters" in profile_dict:
            matching_clusters = find_matching(selected=profile_dict["selected_clusters"],
                                              all=current_profile["ml_model"]["clusters"])
            if len(matching_clusters) != len(profile_dict["selected_clusters"]):
                raise HTTPException(status_code=400, detail='Invalid clusters selection')
            profile_dict["clusters"] = matching_clusters
            del profile_dict["selected_clusters"]

        update_result = request.app.db["cluster_profiles"].update_one({"_id": cpid}, {"$set": profile_dict})

        if update_result.modified_count == 1 or update_result.matched_count == 1:
            profiles = list(request.app.db["cluster_profiles"].aggregate(pipeline))
            return profiles[0]

    except bson.errors.InvalidId:
        raise HTTPException(status_code=400, detail='Invalid ID')


@router.delete("/profile/{cluster_profile_id}")
def delete_cluster_profile(request: Request, cluster_profile_id: str):
    try:
        cpid = PyObjectId(cluster_profile_id)
        res = request.app.db["cluster_profiles"].delete_one({"_id": cpid})
        if res.deleted_count == 0:
            raise HTTPException(status_code=400, detail='Smart meter not found.')
        return {"message": "cluster profile deleted successfully"}
    except bson.errors.InvalidId:
        raise HTTPException(status_code=400, detail='Invalid ID')


@router.get("/{ml_model_id}", response_model=List[ClusterProfileRes], response_model_by_alias=False)
def get_cluster_profiles(request: Request, ml_model_id: str):
    try:
        # lookup pipeline
        mid = PyObjectId(ml_model_id)
        pipeline = [
            {
                "$match": {"ml_model_id": mid}
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
                "$unwind": "$ml_model"
            },
            {
                "$project": {
                    "ml_model.clusters": 0,
                    "ml_model_id": 0,
                }
            }
        ]

        results = list(request.app.db["cluster_profiles"].aggregate(pipeline))
        #  response
        return results
        # del new_profile_response["ml_model_id"]
        # del new_profile_response["ml_model"]["clusters"]
        # return new_profile_response
        # created_cluster_profile = request.app.db["cluster_profiles"].find_one({"_id": new_cluster_profile.inserted_id})
    except bson.errors.InvalidId:
        raise HTTPException(status_code=400, detail='Invalid ID')
