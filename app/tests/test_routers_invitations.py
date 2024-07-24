"""
Test Tnvitations Routers
"""

import time
import unittest
from uuid import uuid4
from sqlmodel import Session, select

from app.models import (
    Invitation,
    InvitationStatus,
    Organization,
    User,
    UserOrganizationRole,
    UserRole,
)


from . import client, engine, generate_user_token, TestClient, get_db_override


class TestInvitationsRouters(unittest.TestCase):
    organization_id = uuid4()
    user_email = "test@emad.com"
    user_id = uuid4()
    invited_user_email = "tut@test.com"

    def tearDown(self) -> None:
        """
        Clean up the database after each test
        """
        with Session(engine) as db:
            db.exec(Invitation.__table__.delete())
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

    def test_create_invitation_errors(self):
        """
        Test create invitation errors
        """
        response = client.post(
            f"/organizations/{uuid4()}/invitations/",
            json={"email": self.invited_user_email},
        )
        assert response.status_code == 401
        assert response.json() == {"detail": "Organization not found"}

        response = client.post(
            f"/organizations/{self.organization_id}/invitations/",
            json={"email": self.invited_user_email},
        )
        assert response.status_code == 404

        response = client.post(
            f"/organizations/{self.organization_id}/invitations/",
            json={"email": self.user_email},
        )
        assert response.status_code == 400
        assert response.json() == {
            "detail": "User is already a member of the organization"
        }

        not_allowed_user = {
            "sub": "1234567891",
            "name": "Test User",
            "email": "not_allowed@test.com",
            "exp": time.time() + 60 * 60,
        }

        with Session(engine) as db:
            user = User(
                id=uuid4(),
                name=not_allowed_user["name"],
                email=not_allowed_user["email"],
                image_url="url1",
            )
            user_org = UserOrganizationRole(
                user_id=user.id,
                organization_id=self.organization_id,
                user_role=UserRole.staff,
            )

            db.add_all([user, user_org])
            db.commit()
        new_client = TestClient(
            client.app,
            cookies={"next-auth.session-token": generate_user_token(not_allowed_user)},
        )
        response = new_client.post(
            f"/organizations/{self.organization_id}/invitations/",
            json={"email": self.invited_user_email},
        )

        assert response.status_code == 401
        assert response.json() == {
            "detail": "User is not allowed to invite to the organization"
        }

    def test_create_invitation(self):
        """
        Test create invitation
        """
        invited_user_id = uuid4()
        # create invited user
        with Session(engine) as db:
            user = User(
                id=invited_user_id,
                name="Test User",
                email=self.invited_user_email,
                image_url="url1",
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        response = client.post(
            f"/organizations/{self.organization_id}/invitations/",
            json={"email": self.invited_user_email},
        )

        assert response.status_code == 201

        with Session(engine) as db:
            invitation = db.exec(
                select(Invitation).where(
                    Invitation.user_id == invited_user_id,
                    Invitation.organization_id == self.organization_id,
                )
            ).first()
            assert invitation is not None
            assert invitation.role == UserRole.staff
            assert invitation.status == "pending"

        response = client.post(
            f"/organizations/{self.organization_id}/invitations/",
            json={"email": self.invited_user_email},
        )

        assert response.status_code == 400
        assert response.json() == {
            "detail": "User has already been invited to the organization"
        }

    def test_get_user_invitations(self):
        """
        Test get invitations
        """

        response = client.get(f"/invitations/")

        assert response.status_code == 200
        assert len(response.json()) == 0

        inviter_email = "inviter_email@test.com"
        inviter_id = uuid4()

        # inviter user and organization
        with Session(engine) as db:
            user = User(
                id=inviter_id,
                name="Inviter User",
                email=inviter_email,
                image_url="url1",
            )

            org = Organization(
                id=uuid4(),
                name="Organization 2",
                owner=user.id,
                contact_email="org@test.com",
            )

            user_org_role = UserOrganizationRole(
                user_id=user.id,
                organization_id=org.id,
                user_role=UserRole.creator,
            )

            invitation = Invitation(
                user_id=self.user_id,
                inviter_id=inviter_id,
                organization_id=org.id,
            )

            db.add_all([user, org, user_org_role, invitation])

            db.commit()

        response = client.get(f"/invitations/")

        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_accept_invitation(self):
        """
        Test accept invitation
        """
        # create invited user
        inviter_email = "inviter_email@test.com"
        inviter_id = uuid4()
        invitation_id = uuid4()
        with Session(engine) as db:
            user = User(
                id=inviter_id,
                name="Inviter User",
                email=inviter_email,
                image_url="url1",
            )

            org = Organization(
                id=uuid4(),
                name="Organization 2",
                owner=user.id,
                contact_email="org@test.com",
            )

            user_org_role = UserOrganizationRole(
                user_id=user.id,
                organization_id=org.id,
                user_role=UserRole.creator,
            )

            invitation = Invitation(
                id=invitation_id,
                user_id=self.user_id,
                inviter_id=inviter_id,
                organization_id=org.id,
            )

            db.add_all([user, org, user_org_role, invitation])

            db.commit()

        response = client.put(
            f"/invitations/{invitation_id}", json={"status": "accepted"}
        )

        assert response.status_code == 204
