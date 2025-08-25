from sqlalchemy import Column, BigInteger, String, LargeBinary, TIMESTAMP, text, Integer
from sqlalchemy.dialects.mysql import TINYINT
from src.db.session import Base

class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    uid = Column(LargeBinary(length=4), nullable=False, unique=True)

    name = Column(String(10), nullable=False)

    created_at = Column(
        TIMESTAMP,
        nullable=False,
        server_default=text('CURRENT_TIMESTAMP')
    )

class UserSetting(Base):
    __tablename__ = "user_setting"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String())
    bright = Column(TINYINT)
    blind = Column(TINYINT)
    window = Column(TINYINT)
    last_presence = Column(TIMESTAMP)