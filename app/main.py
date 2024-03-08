from fastapi import FastAPI
from sqlmodel import Session, create_engine, SQLModel
from app.models.user import User
from app.models.organization import Organization
from app.models.link_models import UserOrganization

api = FastAPI()


@api.get("/")
def read_root():
    return {"Hello": "World"}


sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, echo=True)

SQLModel.metadata.create_all(engine)

with Session(engine) as session:

    user_1 = User(email="email1", name="name1", image_url="url1")
    user_2 = User(email="email2", name="name2", image_url="url2")
    user_3 = User(email="email3", name="name3", image_url="url3")

    session.add_all([user_1, user_2, user_3])

    organization_1 = Organization(name="organization1", owner=user_1.id)
    organization_2 = Organization(name="organization2", owner=user_2.id)
    organization_3 = Organization(name="organization3", owner=user_3.id)

    session.add_all([organization_1, organization_2, organization_3])

    user_organization_1 = UserOrganization(
        user_id=user_1.id, organization_id=organization_1.id
    )
    user_organization_2 = UserOrganization(
        user_id=user_2.id, organization_id=organization_2.id
    )

    session.add_all([user_organization_1, user_organization_2])
    session.commit()
