import json
import pytest
from app.models.meters import MeterRes
from bson import ObjectId

TEST_METER = {
    "device_id": "test_id_2",
    "contract_pw": 16,
    "prod_pw": 2,
    "type": "commercial"
}

# EXISTING_TEST_DATA = [
#     {
#         "device_id": "test_id_0",
#         "contract_pw": 16,
#         "prod_pw": 2,
#         "type": "commercial"
#     },
#     {
#         "device_id": "test_id_1",
#         "contract_pw": 16,
#         "prod_pw": 2,
#         "type": "public"
#     }]

UPDATED_SMART_METER = {
    "device_id": "test_id_4",
    "contract_pw": 17,
    "prod_pw": 0,
    "type": "public2"
}


# @pytest.fixture(scope="module")
# def test_create_meter(test_client):
#     test_meter_1 = EXISTING_TEST_DATA[0].copy()
#     test_meter_2 = EXISTING_TEST_DATA[1].copy()
#     try:
#         # INSERT A SAMPLE TO DB TO TEST GET, UPDATE, DELETE
#         new_meters = test_client.app.db["meters"].insert_many([test_meter_1, test_meter_2])
#         registered_meter_1 = test_client.app.db["meters"].find_one({"_id": new_meters.inserted_ids[0]})
#         registered_meter_2 = test_client.app.db["meters"].find_one({"_id": new_meters.inserted_ids[1]})
#         yield registered_meter_1, registered_meter_2
#     except Exception as e:
#         raise e
#     else:
#         test_client.app.db["meters"].delete_one({"_id": new_meters.inserted_ids[0]})
#         test_client.app.db["meters"].delete_one({"_id": new_meters.inserted_ids[1]})


def test_get_all_meters(test_client):
    db_meters = list(test_client.app.db["meters"].find())
    response = test_client.get("/meters/all")
    assert response.status_code == 200
    meters = response.json()
    assert isinstance(meters, list)
    assert len(meters) == len(db_meters), "ListS lengths mismatch"
    meters.sort(key=lambda x: x['id'])
    db_meters.sort(key=lambda x: str(x['_id']))
    for idx, meter in enumerate(meters):
        assert meter['id'] == str(db_meters[idx]['_id'])
        assert all(meter[key] == db_meters[idx][key] for key in MeterRes.__fields__ if key not in ['id', '_id'])


def test_create_meter_twice(test_client):
    found_meter = None
    try:
        response = test_client.post("/meters/meter", content=json.dumps(TEST_METER))
        assert response.status_code == 200, "New smart meter creation failed"
        meters = response.json()
        # requirement for frontend (REST violation)
        assert len(meters) >= 1, "List length invalid"
        found_meter = next((item for item in meters if item['device_id'] == TEST_METER["device_id"]), None)
        assert found_meter is not None, "Meter not found in response"
        response = test_client.post("/meters/meter", content=json.dumps(TEST_METER))
        assert response.status_code == 400, "Device with same id was inserted."
        assert response.json() == {"detail": "Device id already exists"}
    finally:
        if found_meter is not None:
            deleted = test_client.app.db["meters"].delete_one({"_id": ObjectId(found_meter['id'])})
            assert deleted.deleted_count == 1, "No documents deleted"


def test_get_meter_by_id(test_client):
    db_smart_meter = test_client.app.db['meters'].find_one()
    sm_id = str(db_smart_meter['_id'])
    response = test_client.get(f"/meters/{sm_id}")
    assert response.status_code == 200
    smart_meter = response.json()
    assert smart_meter.pop('id') == str(db_smart_meter.pop('_id')), "Ids mismatch"
    assert all(smart_meter[key] == db_smart_meter[key] for key in MeterRes.__fields__ if key not in ['_id', 'id'])


def test_delete_meter(test_client):
    db_smart_meter = test_client.app.db["meters"].find_one()
    sm_id = str(db_smart_meter['_id'])
    response = test_client.delete(f"/meters/{sm_id}")
    assert response.status_code == 200, f'Delete operation failed with {response}'
    # frontend list requirement
    meters = response.json()
    assert isinstance(meters, list), "Delete response is not a list"
    response = test_client.get(f"/meters/{sm_id}")
    assert response.status_code == 200
    assert response.json() is None
    meter = test_client.app.db["meters"].find_one({'_id': db_smart_meter['_id']})
    assert meter is None, 'Meter not deleted from database'


def test_update_meter(test_client):
    db_smart_meter = test_client.app.db['meters'].find_one()
    smart_meter_id = str(db_smart_meter['_id'])
    updated_smart_meter = {**{'id': smart_meter_id, **UPDATED_SMART_METER}}
    response = test_client.put(f'/meters/{smart_meter_id}', content=json.dumps(updated_smart_meter))
    # front-end requirement (return a list)
    smart_meters = response.json()
    count = sum(1 for meter in smart_meters if meter['id'] == smart_meter_id)
    assert count == 1
    returned_smart_meter = next((item for item in smart_meters if item['id'] == smart_meter_id), None)
    db_smart_meter_updated = test_client.app.db['meters'].find_one({'_id': ObjectId(smart_meter_id)})
    assert returned_smart_meter['id'] == str(db_smart_meter_updated['_id'])
    assert all(returned_smart_meter[key] == UPDATED_SMART_METER[key] for key in UPDATED_SMART_METER)
    assert all(db_smart_meter_updated[key] == UPDATED_SMART_METER[key] for key in UPDATED_SMART_METER)
