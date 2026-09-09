"""initial tables

Revision ID: 2d95cef0c8f6
Revises:
Create Date: 2026-09-09

municipalities / rent_statistics / land_price_points / real_estate_transactions を作成する。
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "2d95cef0c8f6"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "municipalities",
        sa.Column("municipality_code", sa.String(length=5), nullable=False),
        sa.Column("prefecture_code", sa.String(length=2), nullable=True),
        sa.Column("prefecture_name", sa.String(length=50), nullable=False),
        sa.Column("municipality_name", sa.String(length=100), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("municipality_code"),
    )

    op.create_table(
        "rent_statistics",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("municipality_code", sa.String(length=5), nullable=False),
        sa.Column("survey_year", sa.Integer(), nullable=False),
        sa.Column("average_rent", sa.Integer(), nullable=True),
        sa.Column("source", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["municipality_code"], ["municipalities.municipality_code"]
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "municipality_code", "survey_year", name="uq_rent_statistics_muni_year"
        ),
    )
    op.create_index(
        "ix_rent_statistics_muni_year",
        "rent_statistics",
        ["municipality_code", "survey_year"],
        unique=False,
    )

    op.create_table(
        "land_price_points",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("municipality_code", sa.String(length=5), nullable=False),
        sa.Column("survey_year", sa.Integer(), nullable=False),
        sa.Column("price_per_sqm", sa.Integer(), nullable=False),
        sa.Column("latitude", sa.Double(), nullable=True),
        sa.Column("longitude", sa.Double(), nullable=True),
        sa.Column("land_price_type", sa.String(length=50), nullable=True),
        sa.Column("source", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["municipality_code"], ["municipalities.municipality_code"]
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_land_price_points_muni_year",
        "land_price_points",
        ["municipality_code", "survey_year"],
        unique=False,
    )

    op.create_table(
        "real_estate_transactions",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("municipality_code", sa.String(length=5), nullable=False),
        sa.Column("transaction_year", sa.Integer(), nullable=False),
        sa.Column("transaction_quarter", sa.Integer(), nullable=True),
        sa.Column("district_name", sa.String(length=255), nullable=True),
        sa.Column("property_type", sa.String(length=100), nullable=False),
        sa.Column("trade_price", sa.BigInteger(), nullable=True),
        sa.Column("area_sqm", sa.Double(), nullable=True),
        sa.Column("unit_price", sa.Integer(), nullable=True),
        sa.Column("station_name", sa.String(length=255), nullable=True),
        sa.Column("station_minutes", sa.Integer(), nullable=True),
        sa.Column("source", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["municipality_code"], ["municipalities.municipality_code"]
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_real_estate_transactions_muni_year",
        "real_estate_transactions",
        ["municipality_code", "transaction_year"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_real_estate_transactions_muni_year",
        table_name="real_estate_transactions",
    )
    op.drop_table("real_estate_transactions")
    op.drop_index(
        "ix_land_price_points_muni_year", table_name="land_price_points"
    )
    op.drop_table("land_price_points")
    op.drop_index(
        "ix_rent_statistics_muni_year", table_name="rent_statistics"
    )
    op.drop_table("rent_statistics")
    op.drop_table("municipalities")
