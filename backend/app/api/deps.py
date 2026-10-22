from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models import InstitutionUser, Institution
from app.schemas.auth import TokenPayload

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> InstitutionUser:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = TokenPayload(sub=user_id, role=payload.get("role"), institution_id=payload.get("institution_id"))
    except jwt.PyJWTError:
        raise credentials_exception

    user = db.query(InstitutionUser).filter(InstitutionUser.id == int(token_data.sub)).first()
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user account")
    return user


def require_roles(allowed_roles: list[str]):
    def role_checker(current_user: InstitutionUser = Depends(get_current_user)) -> InstitutionUser:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Requires one of roles: {', '.join(allowed_roles)}"
            )
        return current_user
    return role_checker

def verify_institution_access(institution_id: int, current_user: InstitutionUser):
    """Enforces tenant boundary: institutional users can only access their own institution."""
    if current_user.role in ["AICTE_ADMIN", "REGIONAL_OFFICER"]:
        return  # Regulators have cross-institutional oversight
    if current_user.institution_id != institution_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You can only access records belonging to your assigned institution."
        )
