"""
This module covers the root endpoint tests
"""
import unittest
from . import client, user


class TestRootEndpoint(unittest.TestCase):
    """
    This class covers the root endpoint tests
     - test_root_endpoint
    """

    def test_root_endpoint(self):
        """
        Test root endpoint
        """
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"Hello": f"{user['name']}, {user['email']}"}
