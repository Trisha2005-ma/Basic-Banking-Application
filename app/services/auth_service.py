import secrets
from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import create_access_token, hash_password, verify_password
from app.models import Account, User
from app.repositories.account_repository import AccountRepository
from app.repositories.token_repository import TokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)
        self.accounts = AccountRepository(db)
        self.tokens = TokenRepository(db)

    def _generate_account_number(self) -> str:
        while True:
            number = "".join(str(secrets.randbelow(10)) for _ in range(10))
            if not self.accounts.account_number_exists(number):
                return number

    def register(self, data: RegisterRequest) -> tuple[User, Account]:
        if self.users.get_by_email(data.email):
            raise ConflictError("Email is already registered")
        try:
            user = self.users.create(data.name, data.email, hash_password(data.password))
            account = self.accounts.create(user.id, self._generate_account_number())
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise ConflictError("Email is already registered")
        return user, account

    def login(self, data: LoginRequest) -> str:
        user = self.users.get_by_email(data.email)
        if user is None or not verify_password(data.password, user.password_hash):
            raise UnauthorizedError("Invalid email or password")
        return create_access_token(user.id)

    def logout(self, payload: dict) -> None:
        expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        self.tokens.delete_expired()
        self.tokens.add(payload["jti"], expires_at)
        self.db.commit()
