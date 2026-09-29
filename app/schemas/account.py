from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import Field

from app.schemas.base import CamelModel

Amount = Annotated[Decimal, Field(gt=0, max_digits=12, decimal_places=2)]


class AmountRequest(CamelModel):
    amount: Amount


class TransferRequest(CamelModel):
    receiver_account_id: Annotated[int, Field(gt=0)]
    amount: Amount


class AccountResponse(CamelModel):
    account_id: int
    account_number: str
    account_holder_name: str
    balance: float
    created_at: datetime
