import uuid
from datetime import datetime

import sqlalchemy as sa
from pydantic import ConfigDict
from sqlalchemy.sql import func
from sqlmodel import Field, SQLModel


class ModelBase(SQLModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
    )

    created_date: datetime | None = Field(
        default=None,
        sa_type=sa.DateTime(timezone=True),
        sa_column_kwargs={"server_default": func.now()},
        nullable=False,
        alias="created date",
    )

    updated_date: datetime | None = Field(
        default=None,
        sa_type=sa.DateTime(timezone=True),
        sa_column_kwargs={"server_default": func.now()},
        nullable=False,
        alias="last updated",
    )
