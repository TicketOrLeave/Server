"""
Test Organization routers
"""

import time
import unittest
from uuid import uuid4
from sqlmodel import Session, select

from app.models import (
    Invitation,
    Organization,
    User,
    UserOrganizationRole,
    UserRole,
)


from . import (
    client,
    engine,
    generate_user_token,
    TestClient,
)


class TestOrganizationsRouters(unittest.TestCase):
    organization_id = uuid4()
    user_email = "test@emad.com"
    user_id = uuid4()

    def tearDown(self) -> None:
        """
        Clean up the database after each test
        """
        with Session(engine) as db:
            db.exec(
                Organization.__table__.delete().where(
                    Organization.id != self.organization_id
                )
            )
            db.exec(User.__table__.delete().where(User.email != self.user_email))
            db.commit()

    @classmethod
    def setUpClass(cls):
        """
        Create organization and user for testing
        """
        with Session(engine) as db:
            user = User(
                id=cls.user_id,
                name="Emad Anwer",
                email=cls.user_email,
                image_url="url1",
            )
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
            db.exec(Organization.__table__.delete())
            db.exec(User.__table__.delete())
            db.exec(Invitation.__table__.delete())
            db.commit()

    def test_get_user_organizations(self):
        response = client.get("/organizations")
        assert response.status_code == 200
        assert len(response.json()) == 1

        with Session(engine) as db:
            org = Organization(
                id=uuid4(),
                name="Organization 2",
                owner=self.user_id,
                contact_email="test@mail.com",
            )

            user_org = UserOrganizationRole(
                user_id=self.user_id,
                organization_id=org.id,
                user_role=UserRole.creator,
            )
            db.add_all([org, user_org])

            db.commit()

        response = client.get("/organizations")
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_get_organization(self):
        response = client.get(f"/organizations/{self.organization_id}")
        assert response.status_code == 200
        assert response.json()["id"] == str(self.organization_id)

        response = client.get(f"/organizations/{uuid4()}")
        assert response.status_code == 404

    def test_get_organization_members(self):
        response = client.get(f"/organizations/{self.organization_id}/members")
        assert response.status_code == 200
        assert len(response.json()) == 1

        with Session(engine) as db:
            user = User(
                id=uuid4(),
                name="User 1",
                email="ali@test.com",
                image_url="url2",
            )

            org_role = UserOrganizationRole(
                user_id=user.id,
                organization_id=self.organization_id,
                user_role=UserRole.staff,
            )
            db.add_all([user, org_role])
            db.commit()

        response = client.get(f"/organizations/{self.organization_id}/members")
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_create_organization(self):
        response = client.post(
            "/organizations/",
            json={"name": "Organization 2", "contact_email": "org2@test.com"},
        )

        assert response.status_code == 200
        assert response.json()["name"] == "Organization 2"

    def test_create_organization_with_invalid_data(self):
        response = client.post("/organizations/", json={})
        assert response.status_code == 422

    def test_change_user_role(self):

        user_id = uuid4()
        with Session(engine) as db:
            user = User(
                id=user_id,
                name="User 1",
                email="ali@test.com",
                image_url="url2",
            )

            org_role = UserOrganizationRole(
                user_id=user.id,
                organization_id=self.organization_id,
                user_role=UserRole.staff,
            )

            db.add_all([user, org_role])
            db.commit()

        response = client.put(
            f"/organizations/{self.organization_id}/members/{user_id}",
            json={"role": "admin"},
        )

        assert response.status_code == 204

    def test_change_user_role_errors(self):
        response = client.put(
            f"/organizations/{self.organization_id}/members/{self.user_id}",
            json={},
        )

        assert response.status_code == 422

        response = client.put(
            f"/organizations/{self.organization_id}/members/{uuid4()}",
            json={"role": "admin"},
        )

        assert response.status_code == 401
        assert response.json() == {"detail": "User not found in the organization"}

        response = client.put(
            f"/organizations/{self.organization_id}/members/{self.user_id}",
            json={"role": "admin"},
        )
        assert response.status_code == 401
        assert response.json() == {"detail": "User cannot change their own role"}

        new_user_id = uuid4()
        other_user_id = uuid4()

        with Session(engine) as db:
            user = User(
                id=new_user_id,
                name="User 1",
                email="not_allowed@test.com",
                image_url="url2",
            )
            user2 = User(
                id=other_user_id,
                name="User 2",
                email="other@user.com'",
                image_url="url3",
            )

            db.add_all(
                [
                    user,
                    user2,
                    UserOrganizationRole(
                        user_id=user.id,
                        organization_id=self.organization_id,
                        user_role=UserRole.staff,
                    ),
                    UserOrganizationRole(
                        user_id=user2.id,
                        organization_id=self.organization_id,
                        user_role=UserRole.staff,
                    ),
                ]
            )
            db.commit()

        new_user = {
            "sub": "1234567891",
            "name": "Test User",
            "email": "not_allowed@test.com",
            "exp": time.time() + 60 * 60,
        }
        new_client = TestClient(
            client.app,
            cookies={"next-auth.session-token": generate_user_token(new_user)},
        )

        response = new_client.put(
            f"/organizations/{self.organization_id}/members/{other_user_id}",
            json={"role": "admin"},
        )

        assert response.status_code == 401
        assert response.json() == {"detail": "User is not authorized to change roles"}

        response = new_client.put(
            f"/organizations/{self.organization_id}/members/{uuid4()}",
            json={"role": "admin"},
        )

        assert response.status_code == 401
        assert response.json() == {"detail": "User not found in the organization"}

        with Session(engine) as db:
            user_role = db.exec(
                select(UserOrganizationRole)
                .where(UserOrganizationRole.user_id == self.user_id)
                .where(UserOrganizationRole.organization_id == self.organization_id)
            ).first()

            user_role.user_role = UserRole.admin

            user_role2 = db.exec(
                select(UserOrganizationRole)
                .where(UserOrganizationRole.user_id == other_user_id)
                .where(UserOrganizationRole.organization_id == self.organization_id)
            ).first()

            user_role2.user_role = UserRole.admin
            db.add_all([user_role, user_role2])
            db.commit()

        response = new_client.put(
            f"/organizations/{self.organization_id}/members/{other_user_id}",
            json={"role": "admin"},
        )

        assert response.status_code == 401
        assert response.json() == {"detail": "User is not authorized to change roles"}

    def test_remove_user(self):
        user_id = uuid4()
        with Session(engine) as db:
            user = User(id=user_id, name="User 1", email="user@test.com")
            org_role = UserOrganizationRole(
                user_id=user.id,
                organization_id=self.organization_id,
                user_role=UserRole.staff,
            )

            db.add_all([user, org_role])
            db.commit()

        response = client.delete(
            f"/organizations/{self.organization_id}/members/{user_id}"
        )

        assert response.status_code == 204

        response = client.delete(
            f"/organizations/{self.organization_id}/members/{self.user_id}"
        )

        assert response.status_code == 401
