import bson
from fastapi import HTTPException, Request, Body

from app.models.common import PyObjectId
from app.models.cluster_profiles import ClusterProfile


def fetch_cluster_profiles(request: Request, profile: ClusterProfile = Body(...)):
    try:
        # lookup pipeline
        mid = PyObjectId(profile.ml_model_id)
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
