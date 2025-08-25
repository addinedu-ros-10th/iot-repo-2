from sqlalchemy.orm import Session
from src.models import user as user_model
from src.schemas import user as user_schema

def create_user(db: Session, user: user_schema.userCreate):
    db_user = user_model.User(name=user.name, uid=user.uid)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_users(db: Session, limit: int = 100):
    return db.query(user_model.User).limit(limit).all()

def get_user_by_uid(db: Session, uid:bytes):
    return db.query(user_model.User).filter(user_model.User.uid == uid).first()