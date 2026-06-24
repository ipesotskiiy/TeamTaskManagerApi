from app.db.session import get_db


def test_database_layer():
    generator = get_db()
    db = next(generator)
    assert db is not None
    generator.close()
