from sqlalchemy import Column, BigInteger, String, LargeBinary, TIMESTAMP, text
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