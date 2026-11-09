from __future__ import annotations
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.enums import OAuthProvider, enum_column

class OAuthAccount(Base):
	"""One provider identity linked to one user
	
	A user can link several providers to the same account
	
	A given provider identity can belong to only one user ever"""

	__tablename__ = "oauth_accounts"

	id: Mapped[int] = mapped_column(primary_key=True)

	user_id: Mapped[int] = mapped_column(
		ForeignKey("users.id", ondelete="CASCADE"),
		nullable=False
	)

	provider: Mapped[OAuthProvider] = mapped_column(
		enum_column(OAuthProvider, "oauth_provider"),
		nullable=False
	)

	provider_account_id: Mapped[str] = mapped_column(String(255), nullable=False)

	created_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), server_default=func.now(), nullable=False
	)

	__table_args__ = (
		Index("ix_oauth_accounts_user_id", "user_id"),
		UniqueConstraint(provider, provider_account_id,
				   name="uq_oauth_accounts_provider_provider_account_id"),
	)