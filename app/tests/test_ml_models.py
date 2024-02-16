import json
from bson import ObjectId
from app.models.ml_models import MLModelRes

TEST_ML_MODEL = {
    "model_uri": "test_s3_uri",
    "algorithm": "kmeans",
    "clusters_number": 3,
    "creation_date": "2023-09-07",
    "data_start_date": "2023-09-07",
    "data_end_date": "2023-09-07",
    "stop_date": "2023-09-07",
    "clusters": [
        {
            "number": 0,
            "line_data": []
        },
        {
            "number": 1,
            "line_data": []
        },
        {
            "number": 2,
            "line_data": []
        }
    ]
}


def test_get_all_ml_models(test_client):
    db_ml_models_ids = test_client.app.db["ml_models"].find()
    response = test_client.get("/models")
    assert response.status_code == 200
    returned_ml_models = response.json()
    assert isinstance(returned_ml_models, list)
    for idx, m in enumerate(db_ml_models_ids):
        assert all(key in m for key in MLModelRes.__fields__ if key not in ['id', '_id']), "Not all keys returned"
        assert str(m['_id']) == returned_ml_models[idx]['id']


def test_create_ml_model(test_client):
    new_ml_model_id = None
    try:
        response = test_client.post("/models/model", content=json.dumps(TEST_ML_MODEL))
        assert response.status_code == 200, "Ml model insertion failed"
        new_ml_model = response.json()
        assert 'id' in new_ml_model, "ID missing from created ml model"
        new_ml_model_id = new_ml_model.pop('id')
        assert new_ml_model == TEST_ML_MODEL, "missmatch on data returned and data uploaded"
        db_ml_model = test_client.app.db['ml_models'].find_one({'_id': ObjectId(new_ml_model_id)})
        assert all(new_ml_model[key] == db_ml_model[key] for key in MLModelRes.__fields__ if key not in ['id', '_id'])
    finally:
        if new_ml_model_id is not None:
            deleted = test_client.app.db["ml_models"].delete_one({"_id": ObjectId(new_ml_model_id)})
            assert deleted.deleted_count == 1, "No documents deleted"


def test_get_ml_model_by_id(test_client):
    db_ml_model = test_client.app.db["ml_models"].find_one()
    mid = str(db_ml_model['_id'])
    response = test_client.get(f"/models/{mid}")
    assert response.status_code == 200
    returned_ml_model = response.json()
    assert returned_ml_model['id'] == mid
    assert all(returned_ml_model[key] == db_ml_model[key] for key in MLModelRes.__fields__ if key not in ['id', '_id'])
