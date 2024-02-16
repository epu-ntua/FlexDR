from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, constr, Field
from typing import List, Optional
from bson import ObjectId
from .common import PyObjectId
from .ml_models import Cluster, MLModelRes


class Recommendation(BaseModel):
    name: Optional[constr(strip_whitespace=True, max_length=50)] = Field(default="")
    description: Optional[constr(strip_whitespace=True, max_length=100)] = Field(default="")
    details: Optional[constr(strip_whitespace=True, max_length=500)] = Field(default="")


# used for cluster profile creation
class ClusterProfile(BaseModel):
    # id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    ml_model_id: str
    selected_clusters: List[int]
    name: constr(strip_whitespace=True, min_length=1, max_length=50)
    short_description: constr(strip_whitespace=True, min_length=1, max_length=300)
    long_description: constr(strip_whitespace=True, min_length=1, max_length=900)
    recommendation: Recommendation


# used for cluster profile update
class ClusterProfileUpdate(BaseModel):
    # id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    # ml_model_id: str
    selected_clusters: Optional[List[int]]
    name: constr(strip_whitespace=True, min_length=1, max_length=50)
    short_description: Optional[constr(strip_whitespace=True, min_length=1, max_length=300)]
    long_description: Optional[constr(strip_whitespace=True, min_length=1, max_length=500)]
    recommendation: Optional[Recommendation]

    def to_dict(self):
        model_dict = jsonable_encoder(self)
        # Filter out keys with None values
        filtered_dict = {key: value for key, value in model_dict.items() if value is not None}
        return filtered_dict


# used for response
class ClusterProfileRes(BaseModel):
    id: PyObjectId = Field(..., alias="_id")
    ml_model: MLModelRes
    clusters: List[Cluster]
    name: constr(strip_whitespace=True, min_length=1, max_length=50)
    short_description: constr(strip_whitespace=True, min_length=1, max_length=300)
    long_description: constr(strip_whitespace=True, min_length=1, max_length=500)
    recommendation: Recommendation

    class Config:
        json_encoders = {ObjectId: str}
