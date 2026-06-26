from app.core.security import verify_password, get_password_hash
from app.models import User

def test_user_can_be_saved_with_hashed_password(test_session):
    raw_password = "strong-password"
    user_data = {
      "email": "user@example.com",
      "username": "john",
      "hashed_password": get_password_hash(raw_password),
    }

    user = User(**user_data)
    test_session.add(user)
    test_session.commit()
    test_session.refresh(user)

    assert isinstance(user, User)
    assert user.hashed_password is not None
    assert user.hashed_password != raw_password
    assert verify_password(raw_password, user.hashed_password)
    assert not verify_password("wrong_password", user.hashed_password)




