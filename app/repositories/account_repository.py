from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Account


class AccountRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, account_id: int) -> Account | None:
        return self.db.get(Account, account_id)

    def get_by_user_id(self, user_id: int) -> Account | None:
        return self.db.scalar(select(Account).where(Account.user_id == user_id))

    def get_for_update(self, account_id: int) -> Account | None:
        """Loads the row and locks it until commit or rollback."""
        stmt = select(Account).where(Account.id == account_id).with_for_update()
        return self.db.scalar(stmt)

    def account_number_exists(self, account_number: str) -> bool:
        stmt = select(Account.id).where(Account.account_number == account_number)
        return self.db.scalar(stmt) is not None

    def create(self, user_id: int, account_number: str) -> Account:
        account = Account(user_id=user_id, account_number=account_number)
        self.db.add(account)
        self.db.flush()
        return account
