from pydantic import BaseModel, constr, Field
from typing import List, Optional
from bson import ObjectId
from .common import PyObjectId


class TimeRange(BaseModel):
    start_time: str
    end_time: str


class LineGraphData(BaseModel):
    x: List[float]
    y: List[float]


class ClusterCreate(BaseModel):
    number: int
    image: str


# TODO prevent modification of number and image. Only append or delete.
class ClusterUpdate(BaseModel):
    number: int
    image: str


# used for creation
class LoadProfileModel(BaseModel):
    # id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: constr(strip_whitespace=True, min_length=1, max_length=50)
    short_description: constr(strip_whitespace=True, max_length=300, min_length=1)
    long_description: constr(strip_whitespace=True, min_length=1, max_length=500)
    number: int
    clusters: List[ClusterCreate]
    recommendation: Optional[constr(strip_whitespace=True, min_length=1, max_length=500)]
    # time_ranges: List[TimeRange]
    # line_graph_data: List[LineGraphData]

    # class Config:
    #     allow_population_by_field_name = True
    #     arbitrary_types_allowed = True
    #     json_encoders = {ObjectId: str}


# used for response
class LoadProfileModelBase(BaseModel):
    id: PyObjectId = Field(..., alias="_id")
    name: str
    short_description: str
    long_description: str
    number: int
    clusters: Optional[List[ClusterCreate]]
    recommendation: Optional[str]

    # time_ranges: List[TimeRange]
    # line_graph_data: List[LineGraphData]

    class Config:
        json_encoders = {ObjectId: str}


# used for update
class LoadProfileUpdateModel(BaseModel):
    # id: PyObjectId = Field(..., alias="_id")
    name: Optional[constr(strip_whitespace=True, min_length=1, max_length=50)]
    short_description: Optional[constr(strip_whitespace=True, max_length=50, min_length=1)]
    long_description: Optional[constr(strip_whitespace=True, min_length=1)]
    number: Optional[int]
    clusters: List[ClusterUpdate]
    recommendation: Optional[constr(strip_whitespace=True, min_length=1, max_length=500)]

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
