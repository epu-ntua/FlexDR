import os
import pytest
from pymongo.database import Database
from pymongo import MongoClient
from fastapi.testclient import TestClient


@pytest.fixture(scope="session", autouse=True)
def test_client():
    from app.main import app
    mongo_client: MongoClient = MongoClient(
        f"mongodb://{os.getenv('MONGO_USER')}:{os.getenv('MONGO_PASS')}@{os.getenv('MONGO_HOST')}:{os.getenv('MONGO_PORT')}/")
    app.db: Database = mongo_client[os.getenv('MONGO_TEST_DB')]
    client = TestClient(app)
    try:
        yield client
    finally:
        print("Closing connection")
        mongo_client.close()


@pytest.fixture(autouse=True)
def setup_teardown(request):
    test_name = request.node.name
    print(f"Setup code for test: {test_name}")
    yield
    print(f"Teardown code for test: {test_name} \n")


def test_with_auto_use():
    print("Hi")
