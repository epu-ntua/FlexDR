from pydantic import BaseModel, constr, Field
from typing import List, Optional
from bson import ObjectId
import datetime
from .common import PyObjectId


class Cluster(BaseModel):
    number: int
    line_data: List[float]


# used for creation
class MLModel(BaseModel):
    # id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    model_uri: constr(strip_whitespace=True, min_length=1, max_length=100)
    algorithm: constr(strip_whitespace=True, min_length=1, max_length=50)
    clusters_number: int = Field(..., ge=2, le=20)
    creation_date: datetime.date
    data_start_date: datetime.date
    data_end_date: datetime.date
    stop_date: datetime.date
    clusters: List[Cluster]


class MLModelRes(MLModel):
    id: PyObjectId = Field(..., alias="_id")
    clusters: Optional[List[Cluster]]

    class Config:
        json_encoders = {ObjectId: str}
