
import sqlite3
from pathlib import Path

# Папка проекта
BASE_DIR = Path(__file__).resolve().parent

# Путь к базе данных
DB_PATH = BASE_DIR / "db" / "materials.sqlite3"

# Путь к SQL-файлу
SCHEMA_PATH = BASE_DIR / "db" / "schema.sql"


def get_connection():
    connection = sqlite3.connect(DB_PATH)

    # Включаем проверку внешних ключей
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


def create_database():
    # Создаём папку для базы данных
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Читаем SQL-код
    sql = SCHEMA_PATH.read_text(encoding="utf-8")

    # Создаём таблицы
    with get_connection() as connection:
        connection.executescript(sql)

    print("База данных успешно создана!")


if __name__ == "__main__":
    create_database()
