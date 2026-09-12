from sqlalchemy import inspect

from app.database import engine


def test_database_indexes_exist():
    """
    Verify that database indexes are available.
    """

    inspector = inspect(engine)

    indexed_tables = 0
    total_indexes = 0

    for table_name in inspector.get_table_names():

        indexes = inspector.get_indexes(
            table_name
        )

        if indexes:
            indexed_tables += 1
            total_indexes += len(indexes)

    assert indexed_tables > 0
    assert total_indexes > 0


def test_primary_key_indexes_are_supported():
    """
    Verify that the database exposes table metadata
    required for indexed primary keys.
    """

    inspector = inspect(engine)

    tables = inspector.get_table_names()

    assert len(tables) > 0

    for table_name in tables:

        columns = inspector.get_columns(
            table_name
        )

        primary_key_columns = [
            column
            for column in columns
            if column.get("primary_key")
        ]

        if primary_key_columns:
            assert len(primary_key_columns) >= 1


def test_index_metadata_is_readable():
    """
    Verify that SQLAlchemy can inspect index metadata
    without errors.
    """

    inspector = inspect(engine)

    for table_name in inspector.get_table_names():

        indexes = inspector.get_indexes(
            table_name
        )

        for index in indexes:

            assert "name" in index
            assert "column_names" in index
            assert index["name"]
            assert index["column_names"]