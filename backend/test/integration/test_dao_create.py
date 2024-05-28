import pytest
from pymongo import MongoClient
from src.util.dao import DAO
from unittest.mock import patch, MagicMock
from pymongo.errors import WriteError, DuplicateKeyError
import pymongo
from src.util.validators import getValidator

@pytest.fixture(scope="function")
def dao():
    client = MongoClient('mongodb://root:root@localhost:27017/')
    db = client["test_db"]
    collection = db["test_collection"]

    mock_validator = {
        '$jsonSchema': {
            'bsonType': 'object',
            'required': ['name', 'email'],
            'properties': {
                'name': {
                    'bsonType': 'string',
                    'description': 'must be a string and is required'
                },
                'email': {
                    'bsonType': 'string',
                    'description': 'must be a string and is required'
                }
            }
        }
    }

    with patch('src.util.dao.getValidator', return_value=mock_validator):
        dao_instance = DAO('test_collection')
        collection.create_index('email', unique=True)
        dao_instance.collection.delete_many({})
        yield dao_instance

    db.drop_collection('test_collection')
    client.close()

class TestDAOCreation:
    # Valid input, both name and email
    def test_create_valid_input(self, dao):
        result = dao.create({'name': 'Jane', 'email': 'jane.doe@gmail.com'})
        assert result is not None
        assert result['name'] == 'Jane'
        assert result['email'] == 'jane.doe@gmail.com'

    # Name is not provided which is required
    def test_create_fail_validation(self, dao):
        with pytest.raises(WriteError):
            dao.create({'email': 'jane.doe@gmail.com'})

    # No input
    def test_create_no_input(self, dao):
        with pytest.raises(WriteError):
            dao.create({})

    # Invalid input, email is missing which is required
    def test_create_invalid_input(self, dao):
        with pytest.raises(WriteError):
            dao.create({'name': 'Jane'})

    # Name should be a string, not int
    def test_create_with_wrong_nametype(self, dao):
        with pytest.raises(WriteError):
            dao.create({'name': 1234, 'email': 'jane.doe@gmail.com'}) 
    
     # Email should be a string, not int
    def test_create_with_wrong_emailtype(self, dao):
        with pytest.raises(WriteError):
            dao.create({'name': 'Jane', 'email': 1234}) 

    # Unique email 
    def test_create_unique_email(self, dao):
        dao.create({'name': 'Jane', 'email': 'jane.doe@gmail.com'})
        with pytest.raises(WriteError):
            dao.create({'name': 'John', 'email': 'jane.doe@gmail.com'})