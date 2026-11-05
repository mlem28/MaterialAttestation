
import csv
import re
from pathlib import Path

from database import get_connection, create_database


BASE_DIR = Path(__file__).resolve().parent

CSV_PATH = BASE_DIR / "source" / "materials_k_import.csv"


# Превращаем текст в число
def parse_number(value):
    text = str(value).replace(" ", "").replace(",", ".")

    match = re.search(r"\d+(?:\.\d+)?", text)

    if match is None:
        raise ValueError(f"Неверное число: {value}")

    return float(match.group())


# Загружаем материалы
def import_materials():

    if not CSV_PATH.exists():
        print("Ошибка: CSV-файл не найден")
        return

    with get_connection() as connection:

        with open(
            CSV_PATH,
            encoding="utf-8-sig",
            newline=""
        ) as file:

            reader = csv.DictReader(file, delimiter=";")

            count = 0

            for row in reader:

                # Получаем тип материала
                material_type = row["Тип материала"].strip()

                # Сохраняем тип
                connection.execute(
                    """
                    INSERT OR IGNORE INTO material_types(name)
                    VALUES (?)
                    """,
                    (material_type,)
                )

                # Получаем ID типа
                type_id = connection.execute(
                    """
                    SELECT id FROM material_types
                    WHERE name = ?
                    """,
                    (material_type,)
                ).fetchone()[0]

                # Данные материала
                name = row["Наименование материала"].strip()
                image = row["Изображение"].strip()

                if image.lower() in ("не указано", "нет"):
                    image = ""

                price = parse_number(row["Цена"])

                stock = int(parse_number(
                    row["Количество на складе"]
                ))

                min_stock = int(parse_number(
                    row["Минимальное количество"]
                ))

                pack_size = int(parse_number(
                    row["Количество в упаковке"]
                ))

                unit = row["Единица измерения"].strip()

                # Не добавляем повторно материал
                existing = connection.execute(
                    """
                    SELECT id FROM materials
                    WHERE name = ? AND type_id = ?
                    """,
                    (name, type_id)
                ).fetchone()

                if existing is not None:
                    continue

                # Записываем материал в БД
                connection.execute(
                    """
                    INSERT INTO materials (
                        name,
                        type_id,
                        image,
                        price,
                        stock,
                        min_stock,
                        pack_size,
                        unit
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        name,
                        type_id,
                        image,
                        price,
                        stock,
                        min_stock,
                        pack_size,
                        unit
                    )
                )

                count += 1

    print(f"Успешно импортировано материалов: {count}")


# Проверяем файл поставщиков
def check_suppliers_file():
    path = BASE_DIR / "source" / "supplier_k_import.txt"

    if not path.exists():
        print("Файл поставщиков не найден!")
        return

    print("\nПервые строки файла поставщиков:")

    with open(path, encoding="utf-8-sig") as file:
        for number, line in enumerate(file, start=1):
            if number > 5:
                break

            print(f"Строка {number}: {line.strip()}")


# Преобразуем рейтинг поставщика в число
def parse_rating(value):
    import re

    text = str(value).strip()
    match = re.search(r"\d+", text)

    if match:
        return int(match.group())

    return None

# Импортируем поставщиков
def import_suppliers():
    import csv

    path = BASE_DIR / "source" / "supplier_k_import.txt"

    if not path.exists():
        print("Файл поставщиков не найден!")
        return

    count = 0
    skipped = 0

    with open(path, encoding="utf-8-sig", newline="") as file:
        reader = csv.reader(file, delimiter=",")
        next(reader, None)

        with get_connection() as connection:
            for line_number, row in enumerate(reader, start=2):

                if len(row) != 5:
                    print(f"Пропущена строка {line_number}: {row}")
                    skipped += 1
                    continue

                name = row[0].strip()
                legal_type = row[1].strip()
                tax_id = row[2].strip()
                rating = parse_rating(row[3])
                start_date = row[4].strip()

                if not name:
                    skipped += 1
                    continue

                existing = connection.execute(
                    """
                    SELECT id FROM suppliers
                    WHERE name = ? AND tax_id = ?
                    """,
                    (name, tax_id)
                ).fetchone()

                if existing:
                    skipped += 1
                    continue

                connection.execute(
                    """
                    INSERT INTO suppliers (
                        name,
                        legal_type,
                        tax_id,
                        quality_rating,
                        start_date
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        name,
                        legal_type,
                        tax_id,
                        rating,
                        start_date
                    )
                )

                count += 1

    print(f"Добавлено поставщиков: {count}")
    print(f"Пропущено строк: {skipped}")


# Проверяем Excel-файл со связями
def check_supplier_relations():
    from openpyxl import load_workbook

    path = (
        BASE_DIR
        / "source"
        / "materialsupplier_k_import.xlsx"
    )

    if not path.exists():
        print("Ошибка: Excel-файл не найден!")
        return

    workbook = load_workbook(
        path,
        read_only=True,
        data_only=True
    )

    try:
        print("Листы Excel:", workbook.sheetnames)

        for sheet in workbook.worksheets:
            print(f"\nЛист: {sheet.title}")
            print("Первые пять строк:")

            for number, row in enumerate(
                sheet.iter_rows(values_only=True),
                start=1
            ):
                if number > 5:
                    break

                print(f"Строка {number}: {row}")
    finally:
        workbook.close()

# Импортируем связи материалов и поставщиков
def import_supplier_relations():
    from openpyxl import load_workbook

    path = (
        BASE_DIR
        / "source"
        / "materialsupplier_k_import.xlsx"
    )

    if not path.exists():
        print("Ошибка: Excel-файл не найден!")
        return

    workbook = load_workbook(
        path,
        read_only=True,
        data_only=True
    )

    added = 0
    duplicates = 0
    not_found = []

    try:
        with get_connection() as connection:
            for sheet in workbook.worksheets:

                # Первая строка содержит заголовки
                rows = sheet.iter_rows(values_only=True)
                next(rows, None)

                for number, row in enumerate(rows, start=2):
                    if len(row) < 2:
                        not_found.append(
                            (sheet.title, number, row)
                        )
                        continue

                    material_name = str(
                        row[0] if row[0] is not None else ""
                    ).strip()

                    supplier_name = str(
                        row[1] if row[1] is not None else ""
                    ).strip()

                    if not material_name or not supplier_name:
                        not_found.append(
                            (sheet.title, number, row)
                        )
                        continue

                    # Ищем материал по названию
                    material = connection.execute(
                        """
                        SELECT id FROM materials
                        WHERE name = ?
                        """,
                        (material_name,)
                    ).fetchall()

                    # Ищем поставщика по названию
                    supplier = connection.execute(
                        """
                        SELECT id FROM suppliers
                        WHERE name = ?
                        """,
                        (supplier_name,)
                    ).fetchall()

                    # Не связываем неоднозначные названия
                    if len(material) != 1 or len(supplier) != 1:
                        not_found.append(
                            (sheet.title, number,
                             material_name, supplier_name)
                        )
                        continue

                    material_id = material[0][0]
                    supplier_id = supplier[0][0]

                    # Проверяем, существует ли связь
                    existing = connection.execute(
                        """
                        SELECT 1 FROM material_suppliers
                        WHERE material_id = ?
                          AND supplier_id = ?
                        """,
                        (material_id, supplier_id)
                    ).fetchone()

                    if existing:
                        duplicates += 1
                        continue

                    connection.execute(
                        """
                        INSERT INTO material_suppliers (
                            material_id,
                            supplier_id
                        )
                        VALUES (?, ?)
                        """,
                        (material_id, supplier_id)
                    )

                    added += 1

            # Если есть нераспознанные строки,
            # откатываем импорт, чтобы не потерять данные
            if not_found:
                connection.rollback()
                print("Импорт отменён: есть несовпадения.")
            else:
                connection.commit()

    finally:
        workbook.close()

    print(f"Новых связей обработано: {added}")
    print(f"Уже существующих связей: {duplicates}")
    print(f"Проблемных строк: {len(not_found)}")

    for item in not_found[:20]:
        print("Проверь:", item)

if __name__ == "__main__":
    import_supplier_relations()

