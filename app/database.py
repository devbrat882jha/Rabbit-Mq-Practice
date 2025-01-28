from typing import Annotated

from fastapi import Depends
from sqlmodel import Session, SQLModel, create_engine
from dotenv import load_dotenv
import os

load_dotenv()

username=os.getenv("DB_USER")
password=os.getenv("DB_PASSWORD")
db_name=os.getenv("DB_NAME")

postgres_user = username
postgres_password = password
postgres_db = db_name
postgres_host = "postgres" 
postgres_port = 5432 

postgres_url = f"postgresql://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_db}"

engine = create_engine(postgres_url)


from app.models import *  

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

create_db_and_tables()


def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]
