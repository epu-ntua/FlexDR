from pydantic import BaseModel, constr, Field
from typing import List, Optional
from bson import ObjectId
from .common import PyObjectId
import datetime
from .ml_models import Cluster, MLModelRes
from .cluster_profiles import Recommendation
from .meters import MeterRes


class ClusterProfile(BaseModel):
    id: PyObjectId = Field(..., alias="_id")
    clusters: List[Cluster]
    cluster: List[Cluster]
    name: constr(strip_whitespace=True, min_length=1, max_length=50)
    short_description: constr(strip_whitespace=True, min_length=1, max_length=300)
    long_description: constr(strip_whitespace=True, min_length=1, max_length=500)
    recommendation: Recommendation


class Assignment(BaseModel):
    meter_id: str
    ml_model_id: str
    cluster_assigned: int
    forecasted_load: Optional[List[float]]
    forecast_date: str


class AssignmentUpdate(BaseModel):
    recommendation: Recommendation


class AssignmentRes(BaseModel):
    id: PyObjectId = Field(..., alias="_id")
    meter_id: PyObjectId
    ml_model_id: PyObjectId
    cluster_assigned: int

    class Config:
        json_encoders = {ObjectId: str}


class AssignmentDetailedRes(BaseModel):
    id: PyObjectId = Field(..., alias="_id")
    meter: MeterRes
    ml_model: MLModelRes
    assigned_cluster: Optional[int]
    assigned_cluster_profile: ClusterProfile
    creation_datetime: datetime.datetime
    forecast_datetime: datetime.datetime
    forecasted_load: Optional[List[float]]

    class Config:
        json_encoders = {ObjectId: str}
