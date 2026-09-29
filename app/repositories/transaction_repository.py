from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Transaction, TransactionStatus


class TransactionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        account_id: int,
        type_: str,
        amount: Decimal,
        reference_id: str | None = None,
    ) -> Transaction:
        transaction = Transaction(
            account_id=account_id,
            type=type_,
            amount=amount,
            status=TransactionStatus.SUCCESS.value,
            reference_id=reference_id,
        )
        self.db.add(transaction)
        self.db.flush()
        return transaction

    def list_for_account(self, account_id: int) -> list[Transaction]:
        stmt = (
            select(Transaction)
            .where(Transaction.account_id == account_id)
            .order_by(Transaction.id)
        )
        return list(self.db.scalars(stmt))
