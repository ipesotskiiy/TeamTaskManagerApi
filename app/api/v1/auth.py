from fastapi import (
    APIRouter,
    Depends,
    status,
    HTTPException,
)
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
)
from app.db.session import get_db
from app.models import User
from app.schemas.auth import Token
from app.schemas.user import UserRead, UserCreate

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post(
    "/register/",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
async def user_register(user_data: UserCreate, session: Session = Depends(get_db)):
    existing_user_email = session.query(User).filter(User.email == user_data.email).first()
    if existing_user_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Данный email уже занят другим пользователем",
        )
    existing_user_username = session.query(User).filter(User.username == user_data.username).first()
    if existing_user_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Данный username уже занят другим пользователем",
        )

    hashed_password = get_password_hash(user_data.password)

    user = User(email=user_data.email, username=user_data.username, hashed_password=hashed_password)

    session.add(user)
    session.commit()
    session.refresh(user)

    return user

@router.post(
    "/login/",
    response_model=Token,
    status_code=status.HTTP_200_OK
)
async def user_login(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_db)):
    user_obj = session.query(User).filter(User.username == form_data.username).first()

    if not user_obj:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверные учётные данные",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(form_data.password, user_obj.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверные учётные данные",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(user_obj.id)
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserRead)
async def get_me(user: User = Depends(get_current_user)):
    return user

