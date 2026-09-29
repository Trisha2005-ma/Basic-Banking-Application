from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.account import AccountResponse, AmountRequest, TransferRequest
from app.schemas.transaction import OperationResponse, TransactionResponse
from app.services.account_service import AccountService

router = APIRouter(tags=["Accounts"])


# Keep the original URLs working while documenting the shorter public routes.
@router.get("/api/account", response_model=AccountResponse, summary="Get account details")
@router.get("/api/accounts/me", response_model=AccountResponse, include_in_schema=False)
def get_my_account(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    account = AccountService(db).get_account(user)
    return AccountResponse(
        account_id=account.id,
        account_number=account.account_number,
        account_holder_name=user.name,
        balance=account.balance,
        created_at=account.created_at,
    )


@router.post("/api/deposit", response_model=OperationResponse, summary="Deposit money")
@router.post("/api/accounts/deposit", response_model=OperationResponse, include_in_schema=False)
def deposit(
    data: AmountRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    account, tx = AccountService(db).deposit(user, data.amount)
    return OperationResponse(
        message="Deposit successful",
        balance=account.balance,
        transaction=TransactionResponse.model_validate(tx),
    )


@router.post("/api/withdraw", response_model=OperationResponse, summary="Withdraw money")
@router.post("/api/accounts/withdraw", response_model=OperationResponse, include_in_schema=False)
def withdraw(
    data: AmountRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    account, tx = AccountService(db).withdraw(user, data.amount)
    return OperationResponse(
        message="Withdrawal successful",
        balance=account.balance,
        transaction=TransactionResponse.model_validate(tx),
    )


@router.post("/api/transfer", response_model=OperationResponse, summary="Transfer money")
@router.post("/api/accounts/transfer", response_model=OperationResponse, include_in_schema=False)
def transfer(
    data: TransferRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    account, tx = AccountService(db).transfer(user, data.receiver_account_id, data.amount)
    return OperationResponse(
        message="Transfer successful",
        balance=account.balance,
        transaction=TransactionResponse.model_validate(tx),
    )


@router.get("/api/accounts/transactions", response_model=list[TransactionResponse])
def get_transactions(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return AccountService(db).history(user)
