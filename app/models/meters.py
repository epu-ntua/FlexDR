from typing import Optional
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, constr, Field
from bson import ObjectId
from .common import PyObjectId


# used for creation
class Meter(BaseModel):
    device_id: constr(strip_whitespace=True, min_length=1, max_length=50)
    contract_pw: float
    prod_pw: float
    type: constr(strip_whitespace=True, min_length=1, max_length=100)


# used for response
class MeterRes(BaseModel):
    id: PyObjectId = Field(..., alias="_id")
    device_id: constr(strip_whitespace=True, min_length=1, max_length=50)
    contract_pw: Optional[float]
    prod_pw: Optional[float]
    type: constr(strip_whitespace=True, min_length=1, max_length=100)

    class Config:
        json_encoders = {ObjectId: str}


# used for update
class MeterUpdate(BaseModel):
    # id: PyObjectId = Field(..., alias="_id")
    device_id: Optional[constr(strip_whitespace=True, min_length=1, max_length=50)]
    contract_pw: Optional[float]
    prod_pw: Optional[float]
    type: Optional[constr(strip_whitespace=True, min_length=1, max_length=100)]

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

    # remove None values
    def to_dict(self):
        model_dict = jsonable_encoder(self)
        # Filter out keys with None values
        filtered_dict = {key: value for key, value in model_dict.items() if value is not None}
        return filtered_dict
