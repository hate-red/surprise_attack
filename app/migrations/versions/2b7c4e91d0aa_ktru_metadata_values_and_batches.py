"""KTRU metadata, concrete values, OKEI codes, indexes and CSV batches

Аддитивная миграция: только новые nullable-колонки, индексы и новые таблицы.
Существующие таблицы и данные не удаляются.

Revision ID: 2b7c4e91d0aa
Revises: 9dc477b9edeb
Create Date: 2026-10-11 02:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '2b7c4e91d0aa'
down_revision: Union[str, Sequence[str], None] = '9dc477b9edeb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # --- positions: метаданные позиции КТРУ ---
    op.add_column('positions', sa.Column('okpd2_code', sa.String(), nullable=True))
    op.add_column('positions', sa.Column('okpd2_name', sa.String(), nullable=True))
    op.add_column('positions', sa.Column('status', sa.String(), nullable=True))
    op.add_column('positions', sa.Column('version', sa.Integer(), nullable=True))
    op.add_column(
        'positions',
        sa.Column('is_template', sa.Boolean(), server_default=sa.text('false'), nullable=False),
    )
    op.add_column('positions', sa.Column('parent_code', sa.String(), nullable=True))
    op.add_column('positions', sa.Column('application_date_start', sa.DateTime(), nullable=True))
    op.add_column('positions', sa.Column('application_date_end', sa.DateTime(), nullable=True))
    op.add_column('positions', sa.Column('rubricators', sa.String(), nullable=True))
    op.create_index('ix_positions_okpd2_code', 'positions', ['okpd2_code'])

    # --- okei: код единицы измерения ---
    op.add_column('okei', sa.Column('code', sa.String(), nullable=True))
    op.create_unique_constraint('uq_okei_code', 'okei', ['code'])

    # --- characteristics: код, тип, вид, тип выбора ---
    op.add_column('characteristics', sa.Column('code', sa.String(), nullable=True))
    op.add_column('characteristics', sa.Column('char_type', sa.Integer(), nullable=True))
    op.add_column('characteristics', sa.Column('kind', sa.Integer(), nullable=True))
    op.add_column('characteristics', sa.Column('choice_type', sa.Integer(), nullable=True))
    op.create_index('ix_characteristics_position_id', 'characteristics', ['position_id'])

    # --- characteristic_values: точное значение и код значения ---
    op.add_column('characteristic_values', sa.Column('concrete_value', sa.Numeric(), nullable=True))
    op.add_column('characteristic_values', sa.Column('value_code', sa.String(), nullable=True))
    op.add_column('characteristic_values', sa.Column('value_format', sa.String(), nullable=True))
    op.create_index(
        'ix_characteristic_values_characteristic_id',
        'characteristic_values',
        ['characteristic_id'],
    )

    # --- additional_characteristics: единица измерения может отсутствовать ---
    op.alter_column(
        'additional_characteristics', 'measure_units',
        existing_type=sa.String(), nullable=True,
    )
    op.create_index(
        'ix_additional_characteristics_category_id',
        'additional_characteristics',
        ['category_id'],
    )

    # --- пакетная обработка CSV ---
    op.create_table(
        'import_batches',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('total_items', sa.Integer(), nullable=False),
        sa.Column('processed_items', sa.Integer(), nullable=False),
        sa.Column('error', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'import_batch_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('batch_id', sa.Integer(), nullable=False),
        sa.Column('row_number', sa.Integer(), nullable=False),
        sa.Column('description', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('result_status', sa.String(), nullable=True),
        sa.Column('ktru_code', sa.String(), nullable=True),
        sa.Column('candidates_count', sa.Integer(), nullable=True),
        sa.Column('result', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('error', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['batch_id'], ['import_batches.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_import_batch_items_batch_id', 'import_batch_items', ['batch_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_import_batch_items_batch_id', table_name='import_batch_items')
    op.drop_table('import_batch_items')
    op.drop_table('import_batches')

    op.drop_index('ix_additional_characteristics_category_id', table_name='additional_characteristics')
    # measure_units остаётся nullable: в данных уже могут быть NULL

    op.drop_index('ix_characteristic_values_characteristic_id', table_name='characteristic_values')
    op.drop_column('characteristic_values', 'value_format')
    op.drop_column('characteristic_values', 'value_code')
    op.drop_column('characteristic_values', 'concrete_value')

    op.drop_index('ix_characteristics_position_id', table_name='characteristics')
    op.drop_column('characteristics', 'choice_type')
    op.drop_column('characteristics', 'kind')
    op.drop_column('characteristics', 'char_type')
    op.drop_column('characteristics', 'code')

    op.drop_constraint('uq_okei_code', 'okei', type_='unique')
    op.drop_column('okei', 'code')

    op.drop_index('ix_positions_okpd2_code', table_name='positions')
    for column in (
        'rubricators', 'application_date_end', 'application_date_start',
        'parent_code', 'is_template', 'version', 'status', 'okpd2_name', 'okpd2_code',
    ):
        op.drop_column('positions', column)
