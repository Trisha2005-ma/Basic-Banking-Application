import uuid
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestError, NotFoundError
from app.models import Account, Transaction, TransactionType, User
from app.repositories.account_repository import AccountRepository
from app.repositories.transaction_repository import TransactionRepository


class AccountService:
    def __init__(self, db: Session):
        self.db = db
        self.accounts = AccountRepository(db)
        self.transactions = TransactionRepository(db)

    def get_account(self, user: User) -> Account:
        account = self.accounts.get_by_user_id(user.id)
        if account is None:
            raise NotFoundError("Account not found")
        return account

    def deposit(self, user: User, amount: Decimal) -> tuple[Account, Transaction]:
        own = self.get_account(user)
        try:
            account = self.accounts.get_for_update(own.id)
            account.balance += amount
            tx = self.transactions.create(account.id, TransactionType.DEPOSIT.value, amount)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return account, tx

    def withdraw(self, user: User, amount: Decimal) -> tuple[Account, Transaction]:
        own = self.get_account(user)
        try:
            account = self.accounts.get_for_update(own.id)
            if account.balance < amount:
                raise BadRequestError("Insufficient balance")
            account.balance -= amount
            tx = self.transactions.create(account.id, TransactionType.WITHDRAW.value, amount)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return account, tx

    def transfer(
        self, user: User, receiver_account_id: int, amount: Decimal
    ) -> tuple[Account, Transaction]:
        sender_own = self.get_account(user)
        if receiver_account_id == sender_own.id:
            raise BadRequestError("Cannot transfer money to your own account")
        if self.accounts.get_by_id(receiver_account_id) is None:
            raise NotFoundError("Receiver account not found")

        try:
            # Lock both rows in a fixed order so two opposite transfers
            # can never wait on each other forever (deadlock).
            locked = {}
            for account_id in sorted([sender_own.id, receiver_account_id]):
                locked[account_id] = self.accounts.get_for_update(account_id)
            sender = locked[sender_own.id]
            receiver = locked[receiver_account_id]

            if sender.balance < amount:
                raise BadRequestError("Insufficient balance")

            sender.balance -= amount
            receiver.balance += amount

            reference = uuid.uuid4().hex
            debit = self.transactions.create(
                sender.id, TransactionType.TRANSFER_DEBIT.value, amount, reference
            )
            self.transactions.create(
                receiver.id, TransactionType.TRANSFER_CREDIT.value, amount, reference
            )
            self.db.commit()  # one commit = all-or-nothing
        except Exception:
            self.db.rollback()
            raise
        return sender, debit

    def history(self, user: User) -> list[Transaction]:
        account = self.get_account(user)
        return self.transactions.list_for_account(account.id)
