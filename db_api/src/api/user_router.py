from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from src.crud import user_crud
from src.models import user as user_model
from src.schemas import user as user_schema
from src.db.session import get_db

router = APIRouter()

@router.post("/users", response_model=user_schema.userInfo, tags=["Users"])
def create_user(user: user_schema.userCreate, db: Session = Depends(get_db)):
    print(f"user.uid (in create_user): {user.uid.hex().upper()}")
    print(f"user.name (in create_user): {user.name}")
    return user_crud.create_user(db=db, user=user)

@router.get("/users", response_model=List[user_schema.userInfo], tags=["Users"])
def read_users(db: Session = Depends(get_db)):
    users = user_crud.get_users(db)
    return users

# @router.get("/users/uid", response_model=user_schema.userSearch, tags=["Users"])
@router.get("/users/uid", tags=["Users"])
def read_user_by_uid(uid: str = Query(...), db: Session=Depends(get_db)):
    try:
        uid_bytes = bytes.fromhex(uid)
    except ValueError:
        raise HTTPException(status_code=400, detail="유효하지 않은 UID 형식입니다.")

    # db_user = user_crud.get_user_by_uid(db, uid=uid_bytes)
    # if db_user is None:
    #     raise HTTPException(status_code=404, detail="User not found")
    # # return user_schema.userInfo.model_validate(db_user)
    # return {
    #     "id": db_user.id,
    #     "name": db_user.name,
    #     "uid": db_user.uid.hex().upper(),
    #     "created_at": db_user.created_at
    # }

    subquery = db.query(user_model.User.name).filter(user_model.User.uid == uid_bytes).scalar_subquery()

    user_name = db.query(subquery).scalar()
    if user_name is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    users_with_same_name = db.query(user_model.User).filter(user_model.User.name == user_name).all()

    result = []
    for user in users_with_same_name:
        result.append(
            {
                "id": user.id,
                "name": user.name,
                "uid": user.uid.hex().upper(),
                "created_at": user.created_at
            }
        )
    return result

@router.get("/users/setting/{name}", response_model=user_schema.userSetting, tags=["Users"])
def read_user_setting(name: str, db: Session = Depends(get_db)):
    db_user_setting = user_crud.get_user_setting_by_name(db, name=name)
    if db_user_setting is None:
        raise HTTPException(status_code=404, detail="User setting not found")
    return db_user_setting