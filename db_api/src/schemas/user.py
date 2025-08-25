from pydantic import BaseModel, field_validator, field_serializer
from typing import Any, Union
from datetime import datetime

class userCreate(BaseModel):
    name: str
    uid: Union[str, bytes]

    @field_validator('uid', mode='before')
    @classmethod
    def hex_to_bytes(cls, v: Any) -> bytes:
        if isinstance(v, str):
            try:
                return bytes.fromhex(v)
            except ValueError:
                raise ValueError("유효한 헥사(hex) 문자열이 아닙니다.")
        if isinstance(v, bytes):
            return v
        raise TypeError("uid는 헥사(hex) 문자열이나 byte여야 합니다.")

class userInfo(BaseModel):
    id: int
    name: str
    uid: bytes
    created_at: datetime

    @field_serializer('uid')
    def serialize_uid(self, uid_bytes: bytes, _info) -> str:
        # 👇 이 디버그 메시지를 추가했습니다!
        print(f"--- !!! serializer가 실행됨! UID: {uid_bytes.hex().upper()} !!! ---")
        return uid_bytes.hex().upper()

    class Config:
        from_attributes = True

class userSearch(BaseModel):
    uid: Union[str, bytes]

    @field_validator('uid', mode='before')
    @classmethod
    def hex_to_bytes(cls, v: Any) -> bytes:
        if isinstance(v, str):
            try:
                return bytes.fromhex(v)
            except ValueError:
                raise ValueError("유효한 헥사(hex) 문자열이 아닙니다.")
        if isinstance(v, bytes):
            return v
        raise TypeError("uid는 헥사(hex) 문자열이나 byte여야 합니다.")