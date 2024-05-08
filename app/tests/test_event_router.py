"""


"""
import unittest

from sqlmodel import Session
from . import client, db_user, get_db_override
from app.models import Organization, UserOrganizationRole, UserRole, Event


class TestEventRouter(unittest.TestCase):
    """
    This class covers the event router tests
     - test_create_event
     - test_get_event
     - test_get_all_events
     - test_update_event
     - test_delete_event
    """
    org_id = None

    def tearDown(self) -> None:
        """
        delete event table
        """
        db: Session = next(get_db_override())
        db.query(Event).delete()

    @classmethod
    def setUpClass(cls):
        """
        Create organization
        """
        db: Session = next(get_db_override())
        org = Organization(name="Organization 1",
                           owner=db_user.id, contact_email="test_org@test.com")
        db.add(org)
        db.commit()
        db.refresh(org)

        db.add(UserOrganizationRole(
            user_id=db_user.id, organization_id=org.id, user_role=UserRole.creator))
        db.commit()

        cls.org_id = str(org.id)

    def test_get_all_events_empty(self):
        """
        Test get all events
        """
        response = client.get("/events/", params={"org_id": self.org_id})
        assert response.status_code == 200
        assert response.json() == []

    def test_create_event(self):
        """
        Test create event
        """
        response = client.post(
            "/events/", json={
                "name": "test event",
                "cover_image_url": "string",
                "description": "string",
                "start_date": "2024-03-20T19:55:51.036Z",
                "end_date": "2024-03-20T19:55:51.036Z",
                "location": "string",
                "max_tickets": 2,
                "orgId": self.org_id
            })
        assert response.status_code == 200
        assert response.json().get("name") == "test event"
        assert response.json().get("organization_id") == self.org_id
        assert response.json().get("status") == "SCHEDULED"
        assert response.json().get("max_tickets") == 2

    def test_get_events(self):
        """
        Test get event
        """
        response = client.get("/events/", params={"org_id": self.org_id})
        assert response.status_code == 200
        assert len(response.json()) == 1
