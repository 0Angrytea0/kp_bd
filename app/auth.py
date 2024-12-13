from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from .database import get_db
from .utils import decode_access_token
from jose import JWTError
from .crud import get_current_user_from_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        user_id = int(user_id_str)
    except (JWTError, ValueError):
        raise credentials_exception

    user = await get_current_user_from_db(db, user_id)
    if not user:
        raise credentials_exception

    return user

async def get_current_admin_user(current_user: dict = Depends(get_current_user)):
    if current_user["role_id"] != 1:
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    return current_user
