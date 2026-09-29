from datetime import datetime

from app.schemas.base import CamelModel


class TransactionResponse(CamelModel):
    id: int
    type: str
    amount: float
    status: str
    reference_id: str | None = None
    created_at: datetime


class OperationResponse(CamelModel):
    message: str
    balance: float
    transaction: TransactionResponse
