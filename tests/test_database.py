
import sqlite3
import tempfile
import unittest
from pathlib import Path

from database import SCHEMA_PATH


class TestDatabase(unittest.TestCase):

    def setUp(self):
        """Создаём отдельную временную базу для каждого теста."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        db_path = Path(self.temp_dir.name) / "test.sqlite3"
        self.connection = sqlite3.connect(db_path)
        self.addCleanup(self.connection.close)

        self.connection.execute("PRAGMA foreign_keys = ON")

        sql = SCHEMA_PATH.read_text(encoding="utf-8")
        self.connection.executescript(sql)

    def test_database_connection(self):
        """Проверяем подключение к тестовой базе."""
        result = self.connection.execute(
            "SELECT 1"
        ).fetchone()

        self.assertEqual(result[0], 1)

    def test_materials_table_exists(self):
        """Проверяем существование таблицы материалов."""
        result = self.connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table' AND name = 'materials'
            """
        ).fetchone()

        self.assertIsNotNone(result)

    def test_foreign_keys_enabled(self):
        """Проверяем включение внешних ключей."""
        result = self.connection.execute(
            "PRAGMA foreign_keys"
        ).fetchone()

        self.assertEqual(result[0], 1)


    def test_material_crud(self):
        """Проверяем добавление, изменение и удаление материала."""

        # Создаём тестовый тип материала
        cursor = self.connection.execute(
            "INSERT INTO material_types (name) VALUES (?)",
            ("Тестовый тип",)
        )
        type_id = cursor.lastrowid

        # 1. Добавляем материал
        cursor = self.connection.execute(
            """
            INSERT INTO materials
            (name, type_id, price, stock, unit)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("Тестовый материал", type_id, 150, 10, "шт")
        )
        material_id = cursor.lastrowid

        # Проверяем добавление
        result = self.connection.execute(
            "SELECT price FROM materials WHERE id = ?",
            (material_id,)
        ).fetchone()

        self.assertEqual(result[0], 150)

        # 2. Изменяем цену
        self.connection.execute(
            "UPDATE materials SET price = ? WHERE id = ?",
            (200, material_id)
        )

        result = self.connection.execute(
            "SELECT price FROM materials WHERE id = ?",
            (material_id,)
        ).fetchone()

        self.assertEqual(result[0], 200)

        # 3. Удаляем материал
        self.connection.execute(
            "DELETE FROM materials WHERE id = ?",
            (material_id,)
        )

        result = self.connection.execute(
            "SELECT id FROM materials WHERE id = ?",
            (material_id,)
        ).fetchone()

        self.assertIsNone(result)

    def test_negative_price(self):
        """Проверяем запрет отрицательной цены."""

        # Создаём тип материала специально для теста
        cursor = self.connection.execute(
            "INSERT INTO material_types (name) VALUES (?)",
            ("Тестовый тип для проверки цены",)
        )

        material_type_id = cursor.lastrowid

        # Проверяем, что отрицательная цена запрещена
        with self.assertRaises(sqlite3.IntegrityError):
            self.connection.execute(
                """
                INSERT INTO materials
                (name, type_id, price, stock, unit)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    "Тест отрицательной цены",
                    material_type_id,
                    -100,
                    10,
                    "шт"
                )
            )

    def test_negative_stock(self):
        """Проверяем запрет отрицательного количества."""

        # Создаём тестовый тип материала
        cursor = self.connection.execute(
            "INSERT INTO material_types (name) VALUES (?)",
            ("Тестовый тип для проверки склада",)
        )

        material_type_id = cursor.lastrowid

        # Пытаемся добавить материал с отрицательным остатком
        with self.assertRaises(sqlite3.IntegrityError):
            self.connection.execute(
                """
                INSERT INTO materials
                (name, type_id, price, stock, unit)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    "Тест отрицательного остатка",
                    material_type_id,
                    150,
                    -50,
                    "шт"
                )
            )

    def test_search_materials(self):
        """Проверяем поиск материалов по названию."""

        # Создаём тестовый тип материала
        cursor = self.connection.execute(
            "INSERT INTO material_types (name) VALUES (?)",
            ("Тестовый тип для поиска",)
        )

        material_type_id = cursor.lastrowid

        # Добавляем два тестовых материала
        self.connection.execute(
            """
            INSERT INTO materials
            (name, type_id, price, stock, unit)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("Тестовая нить", material_type_id, 100, 10, "м")
        )

        self.connection.execute(
            """
            INSERT INTO materials
            (name, type_id, price, stock, unit)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("Тестовый гранулят", material_type_id, 200, 20, "кг")
        )

        # Ищем материал по части названия
        rows = self.connection.execute(
            """
            SELECT name
            FROM materials
            WHERE name LIKE ?
            """,
            ("%нить%",)
        ).fetchall()

        # Проверяем результат поиска
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][0], "Тестовая нить")
    
    def test_materials_pagination(self):
        """Проверяем разделение материалов на страницы."""

        # Создаём тестовый тип материала
        cursor = self.connection.execute(
            "INSERT INTO material_types (name) VALUES (?)",
            ("Тестовый тип для пагинации",)
        )

        material_type_id = cursor.lastrowid

        # Добавляем 25 тестовых материалов
        for i in range(25):
            self.connection.execute(
                """
                INSERT INTO materials
                (name, type_id, price, stock, unit)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    f"Материал {i + 1:02d}",
                    material_type_id,
                    100,
                    10,
                    "шт"
                )
            )

        # Получаем первую страницу
        page_1 = self.connection.execute(
            """
            SELECT name
            FROM materials
            ORDER BY name
            LIMIT 20 OFFSET 0
            """
        ).fetchall()

        # Получаем вторую страницу
        page_2 = self.connection.execute(
            """
            SELECT name
            FROM materials
            ORDER BY name
            LIMIT 20 OFFSET 20
            """
        ).fetchall()

        # Проверяем количество материалов
        self.assertEqual(len(page_1), 20)
        self.assertEqual(len(page_2), 5)

        # Проверяем отсутствие повторений
        names_1 = {row[0] for row in page_1}
        names_2 = {row[0] for row in page_2}

        self.assertTrue(names_1.isdisjoint(names_2))

    def test_invalid_material_type(self):
        """Проверяем запрет несуществующего типа материала."""

        with self.assertRaises(sqlite3.IntegrityError):
            self.connection.execute(
                """
                INSERT INTO materials
                (name, type_id, price, stock, unit)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    "Материал с неверным типом",
                    -999999,
                    100,
                    10,
                    "шт"
                )
            )
        
    def test_null_material_name(self):
        """Проверяем запрет NULL в названии материала."""

        # Создаём тестовый тип материала
        cursor = self.connection.execute(
            "INSERT INTO material_types (name) VALUES (?)",
            ("Тестовый тип для проверки названия",)
        )

        material_type_id = cursor.lastrowid

        # Пытаемся добавить материал без названия
        with self.assertRaises(sqlite3.IntegrityError):
            self.connection.execute(
                """
                INSERT INTO materials
                (name, type_id, price, stock, unit)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    None,
                    material_type_id,
                    100,
                    10,
                    "шт"
                )
            )

if __name__ == "__main__":
    unittest.main()
