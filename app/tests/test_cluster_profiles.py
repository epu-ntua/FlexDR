import json
import pytest
from bson import ObjectId
from app.models.cluster_profiles import ClusterProfileRes, MLModelRes
from .test_ml_models import TEST_ML_MODEL


TEST_DATA = {
    "name": "profile01",
    "short_description": "cluster_profile_test",
    "long_description": "cluster_profile_test",
    "selected_clusters": [0, 1, 2],
    "recommendation": {
        "name": "",
        "description": "",
        "details": ""
    }
}


@pytest.fixture(scope="module")
def ml_model_fixture(test_client):
    try:
        test_ml_model = TEST_ML_MODEL.copy()
        new_ml_model = test_client.app.db["ml_models"].insert_one(test_ml_model)
        inserted_ml_model = test_client.app.db["ml_models"].find_one({"_id": new_ml_model.inserted_id})
        yield inserted_ml_model
    except Exception as e:
        print(e)
    else:
        test_client.app.db["ml_models"].delete_one({"_id": new_ml_model.inserted_id})
    finally:
        print('finally')


# @pytest.fixture(scope="module")
# def cluster_profile_fixture(test_client):
#     try:
#         test_profile = TEST_DATA.copy()
#         ml_models = test_client.app.db["ml_models"].find()
#         test_profile["ml_model_id"] = ml_models[0]['_id']
#         new_profile = test_client.app.db['cluster_profiles'].insert_one(test_profile)
#         created_profile = test_client.app.db['cluster_profiles'].find_one({"_id": new_profile.inserted_id})
#         yield created_profile
#     except Exception as e:
#         raise e
#     else:
#         test_client.app.db["ml_models"].delete_one({"_id": new_profile.inserted_id})


def test_create_cluster_profile(test_client, ml_model_fixture):
    created_cluster = None
    try:
        db_ml_model = ml_model_fixture
        mid = str(db_ml_model['_id'])
        payload = {**TEST_DATA, **{"ml_model_id": mid}}
        response = test_client.post("/cluster-profiles/profile", content=json.dumps(payload))
        assert response.status_code == 200
        created_cluster = response.json()
        assert all(key in created_cluster for key in ClusterProfileRes.__fields__), "Created cluster missing fields"
        # Verify that all selected clusters exist in response
        assert all(cluster['number'] in payload['selected_clusters'] for cluster in
                   created_cluster['clusters']), "Selected clusters missing from response"
        # Verify that ml model is embedded in response and is equal to the one referenced
        assert mid == created_cluster['ml_model']['id']
        assert all(created_cluster['ml_model'][key] == db_ml_model[key] for key in
                   MLModelRes.__fields__ if
                   key not in ['id', '_id', 'clusters']), "Ml model not embedded properly in response"
        # try to create resource again (same clusters should not exist in multiple profiles)
        response = test_client.post("/cluster-profiles/profile", content=json.dumps(payload))
        assert response.status_code == 400, "Logic violation for selected clusters"
    finally:
        if created_cluster is not None and 'id' in created_cluster:
            deleted = test_client.app.db["cluster_profiles"].delete_one({'_id': ObjectId(created_cluster['id'])})
            assert deleted.deleted_count == 1, "No documents deleted"


def test_delete_cluster_profile(test_client):
    db_cluster_profile = test_client.app.db['cluster_profiles'].find_one()
    cp_id = db_cluster_profile['_id']
    response = test_client.delete(f"/cluster-profiles/profile/{str(cp_id)}")
    assert response.status_code == 200
    response = test_client.app.db['cluster_profiles'].find_one({"_id": cp_id})
    assert response is None, 'Cluster profile has not been deleted.'


def test_get_cluster_profiles_by_model_id(test_client):
    # use a cluster profile to get the ml_model referenced
    db_cluster_profile = test_client.app.db["cluster_profiles"].find_one()
    ml_model_id = db_cluster_profile['ml_model_id']
    response = test_client.get(f"/cluster-profiles/{ml_model_id}")
    assert response.status_code == 200, f"Get cluster failed with {response}"
    cluster_profiles = response.json()
    assert len(cluster_profiles) > 0, "No data exist in database"
    for cp in cluster_profiles:
        assert all(key in cp for key in ClusterProfileRes.__fields__)


def test_get_cluster_profile_by_id(test_client):
    db_cluster_profile = test_client.app.db["cluster_profiles"].find_one()
    cp_id = str(db_cluster_profile['_id'])
    response = test_client.get(f"/cluster-profiles/profile/{cp_id}")
    assert response.status_code == 200, f"Get cluster failed with {response}"
    returned_cluster_profile = response.json()
    assert all(key in returned_cluster_profile for key in ClusterProfileRes.__fields__ if key not in ['id', '_id'])
    assert returned_cluster_profile['id'] == cp_id, "Wrong profile returned "
