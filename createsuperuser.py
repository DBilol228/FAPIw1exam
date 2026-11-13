from getpass import getpass
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from app.database import Base, engine, SessionLocal
from app.models import User
from app.schemas import RegisterRequest
from app.security import hash_password

def main():
    username = input("Username: ").strip()
    password = getpass("Password: ")
    confirmation = getpass("Confirm password: ")

    if password != confirmation:
        raise SystemExit("Passwords do not match.")
    try:
        data = RegisterRequest(username=username, password=password)
    except ValidationError as error:
        messages = [
            f"{'.'.join(map(str, item['loc']))}: {item['msg']}"
            for item in error.errors(include_input=False)
        ]
        raise SystemExit("\n".join(messages)) from None

    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        existing = db.scalar(
            select(User).where(User.username == data.username)
        )
        if existing is not None:
            raise SystemExit("Username already exists.")
        user = User(
            username=data.username,
            hashed_password=hash_password(data.password),
            is_active=True,
            is_admin=True,
        )
        db.add(user)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise SystemExit("Could not create user: database constraint conflict.") from None

    print("Superuser created.")

if __name__ == "__main__":
    main()
