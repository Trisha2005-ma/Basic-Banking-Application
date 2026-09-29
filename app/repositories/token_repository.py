from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import BlacklistedToken


class TokenRepository:
    def __init__(self, db: Session):
        self.db = db

    def add(self, jti: str, expires_at: datetime) -> None:
        self.db.add(BlacklistedToken(jti=jti, expires_at=expires_at))
        self.db.flush()

    def is_blacklisted(self, jti: str) -> bool:
        stmt = select(BlacklistedToken.id).where(BlacklistedToken.jti == jti)
        return self.db.scalar(stmt) is not None

    def delete_expired(self) -> None:
        """Expired tokens are rejected anyway, so their rows can go."""
        self.db.execute(
            delete(BlacklistedToken).where(
                BlacklistedToken.expires_at < datetime.now(timezone.utc)
            )
        )
