from fastapi import (
    APIRouter,
    Depends,
    status,
    HTTPException,
)
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
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
def user_register(user_data: UserCreate, session: Session = Depends(get_db)):
    existing_user_email = session.scalar(
        select(User).where(User.email == user_data.email)
    )
    if existing_user_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered",
        )
    existing_user_username = session.scalar(
        select(User).where(User.username == user_data.username)
    )
    if existing_user_username:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username is already registered",
        )

    hashed_password = get_password_hash(user_data.password)

    user = User(email=user_data.email, username=user_data.username, hashed_password=hashed_password)

    session.add(user)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email or username already exists"
        )
    session.refresh(user)

    return user

@router.post(
    "/login/",
    response_model=Token,
    status_code=status.HTTP_200_OK
)
def user_login(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_db)):
    user_obj = session.scalar(
        select(User).where(User.username == form_data.username)
    )

    if user_obj is None or not verify_password(
        form_data.password,
        user_obj.hashed_password,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(user_obj.id)
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me/", response_model=UserRead)
def get_me(user: User = Depends(get_current_user)):
    return user

