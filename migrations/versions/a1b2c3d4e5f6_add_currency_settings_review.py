"""Add currency detection, user settings, and review fields

Revision ID: a1b2c3d4e5f6
Revises: 33bf5b1cbdf8
Create Date: 2026-02-04 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '33bf5b1cbdf8'
branch_labels = None
depends_on = None


def upgrade():
    # Create user_settings table
    op.create_table('user_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('base_currency', sa.String(length=10), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )

    # Add new columns to invoices table
    op.add_column('invoices', sa.Column('currency_confidence', sa.Float(), nullable=True))
    op.add_column('invoices', sa.Column('converted_amount', sa.Numeric(precision=15, scale=2), nullable=True))
    op.add_column('invoices', sa.Column('manually_reviewed', sa.Boolean(), nullable=True))

    # Set default value for manually_reviewed
    op.execute("UPDATE invoices SET manually_reviewed = FALSE WHERE manually_reviewed IS NULL")


def downgrade():
    # Remove columns from invoices table
    op.drop_column('invoices', 'manually_reviewed')
    op.drop_column('invoices', 'converted_amount')
    op.drop_column('invoices', 'currency_confidence')

    # Drop user_settings table
    op.drop_table('user_settings')
