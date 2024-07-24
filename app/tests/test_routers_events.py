"""
Test Event Routes
"""

import datetime
import time
import unittest
from uuid import uuid4
from sqlmodel import Session

from . import client, engine, generate_user_token, TestClient, get_db_override
from app.models import Organization, User, UserOrganizationRole, UserRole, Event


class TestEventRouter(unittest.TestCase):
    """
    This class covers the event router tests
    """

    organization_id = uuid4()

    def tearDown(self) -> None:
        """
        Clean up the database after each test
        """
        with Session(engine) as db:
            db.exec(Event.__table__.delete())
            db.exec(User.__table__.delete().where(User.email != "test@emad.com"))
            db.commit()

    @classmethod
    def setUpClass(cls):
        """
        Create organization and user for testing
        """
        with Session(engine) as db:
            user = User(name="Emad Anwer", email="test@emad.com", image_url="url1")
            db.add(user)
            db.commit()

            org = Organization(
                id=cls.organization_id,
                name="Organization 1",
                owner=user.id,
                contact_email="test_org@test.com",
            )
            db.add(org)
            db.add(
                UserOrganizationRole(
                    user_id=user.id,
                    organization_id=org.id,
                    user_role=UserRole.creator,
                )
            )
            db.commit()

    @classmethod
    def tearDownClass(cls):
        """
        Clean up the database after all tests
        """
        with Session(engine) as db:
            db.exec(UserOrganizationRole.__table__.delete())
            db.exec(Event.__table__.delete())
            db.exec(Organization.__table__.delete())
            db.exec(User.__table__.delete())
            db.commit()

    def test_get_all_events(self):
        """
        get all events for organization
        """
        response = client.get(
            f"organizations/{self.organization_id}/events/",
        )
        assert response.status_code == 200
        assert response.json() == []
        with Session(engine) as db:
            db.add(
                Event(
                    name="test event",
                    cover_image_url="string",
                    description="string",
                    start_date=datetime.datetime.now(),
                    end_date=datetime.datetime.now() + datetime.timedelta(days=1),
                    location="string",
                    max_tickets=2,
                    organization_id=self.organization_id,
                    status="PENDING",
                )
            )
            db.commit()

        response = client.get(
            f"organizations/{self.organization_id}/events/",
        )
        assert response.status_code == 200
        assert len(response.json()) == 1

        with Session(engine) as db:
            db.add(
                Event(
                    name="test event 2",
                    cover_image_url="string",
                    description="string",
                    start_date=datetime.datetime.now(),
                    end_date=datetime.datetime.now() + datetime.timedelta(days=1),
                    location="string",
                    max_tickets=2,
                    organization_id=self.organization_id,
                    status="PENDING",
                )
            )
            db.add(
                Event(
                    name="test event 3",
                    cover_image_url="string",
                    description="string",
                    start_date=datetime.datetime.now(),
                    end_date=datetime.datetime.now() + datetime.timedelta(days=1),
                    location="string",
                    max_tickets=2,
                    organization_id=self.organization_id,
                    status="PENDING",
                )
            )
            db.commit()

        response = client.get(
            f"organizations/{self.organization_id}/events/",
        )
        assert response.status_code == 200
        assert len(response.json()) == 3

    def test_create_event(self):
        """
        Test create event with valid data
        """
        response = client.post(
            f"organizations/{self.organization_id}/events",
            json={
                "name": "test event",
                "cover_image_url": "string",
                "description": "string",
                "start_date": datetime.datetime.now().isoformat(),
                "end_date": (
                    datetime.datetime.now() + datetime.timedelta(days=1)
                ).isoformat(),
                "location": "string",
                "max_tickets": 2,
            },
        )
        assert response.status_code == 200
        assert response.json().get("name") == "test event"
        assert response.json().get("organization_id") == str(self.organization_id)
        assert response.json().get("status") == "PENDING"
        assert response.json().get("max_tickets") == 2

    def test_ceate_event_user_not_in_organization(self):
        """
        Test create event not found
        """
        new_org_id = uuid4()
        with Session(engine) as db:
            new_user = User(
                id=uuid4(), name="Ali Anwer", email="ali@test.com", image_url="url1"
            )
            org = Organization(
                id=new_org_id,
                name="Organization 2",
                owner=new_user.id,
                contact_email="org2@test.com",
            )
            role = UserOrganizationRole(
                user_id=new_user.id, organization_id=org.id, user_role=UserRole.staff
            )
            db.add(new_user)
            db.add(org)
            db.add(role)
            db.commit()

        response = client.post(
            f"organizations/{new_org_id}/events",
            json={
                "name": "test event",
                "cover_image_url": "string",
                "description": "string",
                "start_date": datetime.datetime.now().isoformat(),
                "end_date": (
                    datetime.datetime.now() + datetime.timedelta(days=1)
                ).isoformat(),
                "location": "string",
                "max_tickets": 2,
            },
        )

        assert response.status_code == 404

    def test_create_event_with_invalid_dates(self):
        """
        Test create event with invalid dates
        """
        response = client.post(
            f"organizations/{self.organization_id}/events",
            json={
                "name": "test event",
                "cover_image_url": "string",
                "description": "string",
                "start_date": datetime.datetime.now().isoformat(),
                "end_date": (
                    datetime.datetime.now() - datetime.timedelta(days=1)
                ).isoformat(),
                "location": "string",
                "max_tickets": 2,
            },
        )
        assert response.status_code == 400

    def test_create_event_and_get_all_organization_events(self):
        """
        Test create event and get all organization events
        """
        response = client.post(
            f"organizations/{self.organization_id}/events",
            json={
                "name": "test event",
                "cover_image_url": "string",
                "description": "string",
                "start_date": datetime.datetime.now().isoformat(),
                "end_date": (
                    datetime.datetime.now() + datetime.timedelta(days=1)
                ).isoformat(),
                "location": "string",
                "max_tickets": 2,
            },
        )
        assert response.status_code == 200
        assert response.json().get("name") == "test event"
        assert response.json().get("organization_id") == str(self.organization_id)
        assert response.json().get("status") == "PENDING"
        assert response.json().get("max_tickets") == 2

        client.post(
            f"organizations/{self.organization_id}/events",
            json={
                "name": "test event",
                "cover_image_url": "string",
                "description": "string",
                "start_date": datetime.datetime.now().isoformat(),
                "end_date": (
                    datetime.datetime.now() + datetime.timedelta(days=1)
                ).isoformat(),
                "location": "string",
                "max_tickets": 2,
            },
        )

        response = client.get(
            f"organizations/{self.organization_id}/events/",
        )
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_update_event(self):
        """
        Test update event with valid data
        """
        event_id = uuid4()
        with Session(engine) as db:
            db.add(
                Event(
                    id=event_id,
                    name="test event",
                    cover_image_url="string",
                    description="string",
                    start_date=datetime.datetime.now(),
                    end_date=datetime.datetime.now() + datetime.timedelta(days=1),
                    location="string",
                    max_tickets=2,
                    organization_id=self.organization_id,
                    status="PENDING",
                )
            )
            db.commit()

        response = client.put(
            f"organizations/{self.organization_id}/events/{event_id}",
            json={
                "name": "test event updated",
                "cover_image_url": "string",
                "description": "string",
                "start_date": datetime.datetime.now().isoformat(),
                "end_date": (
                    datetime.datetime.now() + datetime.timedelta(days=1)
                ).isoformat(),
                "location": "string",
                "max_tickets": 2,
                "status": "PENDING",
            },
        )
        assert response.status_code == 200
        assert response.json().get("name") == "test event updated"

    def test_update_event_user_not_in_organization(self):
        """
        Test update event not found in organization
        """
        org_id = uuid4()
        event_id = uuid4()
        with Session(engine) as db:
            user = User(
                id=uuid4(), name="Ali Anwer", email="ali@test.com", image_url="url1"
            )
            org = Organization(
                id=org_id,
                name="Organization 2",
                owner=user.id,
                contact_email="org@test.com",
            )
            role = UserOrganizationRole(
                user_id=user.id, organization_id=org.id, user_role=UserRole.creator
            )
            event = Event(
                id=event_id,
                name="test event",
                cover_image_url="string",
                description="string",
                start_date=datetime.datetime.now(),
                end_date=datetime.datetime.now() + datetime.timedelta(days=1),
                location="string",
                max_tickets=2,
                organization_id=org.id,
                status="PENDING",
            )
            db.add(user)
            db.add(org)
            db.add(role)
            db.add(event)
            db.commit()

        response = client.put(
            f"organizations/{org_id}/events/{event_id}",
            json={
                "name": "test event updated",
                "cover_image_url": "string",
                "description": "string",
                "start_date": datetime.datetime.now().isoformat(),
                "end_date": (
                    datetime.datetime.now() + datetime.timedelta(days=1)
                ).isoformat(),
                "location": "string",
                "max_tickets": 2,
                "status": "PENDING",
            },
        )

        assert response.status_code == 404

    def test_update_event_user_not_owner_or_admin(self):
        """
        Test update event not found in organization
        """
        new_user = {
            "sub": "1234567890",
            "name": "X-Man",
            "email": "test@xman.com",
            "exp": time.time() + 60 * 60,
        }

        with Session(engine) as db:
            new_user_db = User(
                id=uuid4(),
                name=new_user["name"],
                email=new_user["email"],
                image_url="url1",
            )

            new_user_org_role = UserOrganizationRole(
                user_id=new_user_db.id,
                organization_id=self.organization_id,
                user_role=UserRole.staff,
            )

            db.add(new_user_db)
            db.add(new_user_org_role)
            db.commit()

        new_client = TestClient(
            client.app,
            cookies={"next-auth.session-token": generate_user_token(new_user)},
        )
        response = new_client.post(
            f"organizations/{self.organization_id}/events",
            json={
                "name": "test event",
                "cover_image_url": "string",
                "description": "string",
                "start_date": datetime.datetime.now().isoformat(),
                "end_date": (
                    datetime.datetime.now() + datetime.timedelta(days=1)
                ).isoformat(),
                "location": "string",
                "max_tickets": 2,
            },
        )

        assert response.status_code == 401

    def test_update_event_invalid_dates(self):
        """
        Test update event with invalid dates
        """
        event_id = uuid4()
        with Session(engine) as db:
            db.add(
                Event(
                    id=event_id,
                    name="test event",
                    cover_image_url="string",
                    description="string",
                    start_date=datetime.datetime.now(),
                    end_date=datetime.datetime.now() + datetime.timedelta(days=1),
                    location="string",
                    max_tickets=2,
                    organization_id=self.organization_id,
                    status="PENDING",
                )
            )
            db.commit()

        response = client.put(
            f"organizations/{self.organization_id}/events/{event_id}",
            json={
                "name": "test event updated",
                "cover_image_url": "string",
                "description": "string",
                "start_date": datetime.datetime.now().isoformat(),
                "end_date": (
                    datetime.datetime.now() - datetime.timedelta(days=1)
                ).isoformat(),
                "location": "string",
                "max_tickets": 2,
                "status": "PENDING",
            },
        )
        assert response.status_code == 400

    def test_update_event_not_found(self):
        """
        Test update event not found
        """
        response = client.put(
            f"organizations/{self.organization_id}/events/{uuid4()}",
            json={
                "name": "test event updated",
                "cover_image_url": "string",
                "description": "string",
                "start_date": datetime.datetime.now().isoformat(),
                "end_date": (
                    datetime.datetime.now() + datetime.timedelta(days=1)
                ).isoformat(),
                "location": "string",
                "max_tickets": 2,
                "status": "PENDING",
            },
        )
        assert response.status_code == 404

    def test_delete_organization_event(self):
        """
        Test delete event
        """
        response = client.post(
            f"organizations/{self.organization_id}/events",
            json={
                "name": "test event",
                "cover_image_url": "string",
                "description": "string",
                "start_date": datetime.datetime.now().isoformat(),
                "end_date": (
                    datetime.datetime.now() + datetime.timedelta(days=1)
                ).isoformat(),
                "location": "string",
                "max_tickets": 2,
            },
        )
        assert response.status_code == 200
        event_id = response.json().get("id")

        response = client.delete(
            f"organizations/{self.organization_id}/events/{event_id}"
        )
        assert response.status_code == 204

        response = client.get(
            f"organizations/{self.organization_id}/events/",
        )
        assert response.status_code == 200
        assert len(response.json()) == 0

        response = client.delete(
            f"organizations/{self.organization_id}/events/{event_id}"
        )

        assert response.status_code == 404

    def test_delete_organization_event_user_not_in_organization(self):
        """
        Test delete event not found
        """
        other_user = User(
            id=uuid4(), name="Ali Anwer", email="test@ali.com", image_url="url1"
        )
        new_org = Organization(
            id=uuid4(),
            name="Organization 2",
            owner=other_user.id,
            contact_email="test_org@test.com",
        )
        user_org_role = UserOrganizationRole(
            user_id=other_user.id,
            organization_id=new_org.id,
            user_role=UserRole.staff,
        )

        org_event = Event(
            name="test event",
            cover_image_url="string",
            description="string",
            start_date=datetime.datetime.now(),
            end_date=datetime.datetime.now() + datetime.timedelta(days=1),
            location="string",
            max_tickets=2,
            organization_id=new_org.id,
            status="PENDING",
        )

        db: Session = next(get_db_override())

        db.add(new_org)
        db.add(other_user)
        db.add(user_org_role)
        db.add(org_event)

        db.commit()
        response = client.delete(f"organizations/{new_org.id}/events/{org_event.id}")
        assert response.status_code == 404
        assert db.get(Event, org_event.id) is not None

    def test_delete_organization_event_user_not_owner_or_admin(self):
        """
        Test delete event not found
        """
        new_user = {
            "sub": "1234567890",
            "name": "X-Man",
            "email": "test@xman.com",
            "exp": time.time() + 60 * 60,
        }

        with Session(engine) as db:
            new_user_db = User(
                id=uuid4(),
                name=new_user["name"],
                email=new_user["email"],
                image_url="url1",
            )
            db.add(new_user_db)
            db.add(
                UserOrganizationRole(
                    user_id=new_user_db.id,
                    organization_id=self.organization_id,
                    user_role=UserRole.staff,
                )
            )
            db.commit()

        response = client.post(
            f"organizations/{self.organization_id}/events",
            json={
                "name": "test event",
                "cover_image_url": "string",
                "description": "string",
                "start_date": datetime.datetime.now().isoformat(),
                "end_date": (
                    datetime.datetime.now() + datetime.timedelta(days=1)
                ).isoformat(),
                "location": "string",
                "max_tickets": 2,
            },
        )
        assert response.status_code == 200

        token = generate_user_token(new_user)

        cookie = {"next-auth.session-token": token}

        new_client = TestClient(client.app, cookies=cookie)

        event_id = response.json().get("id")

        response = new_client.delete(
            f"organizations/{self.organization_id}/events/{event_id}"
        )
        assert response.status_code == 401
