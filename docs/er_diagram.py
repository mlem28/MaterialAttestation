
from pathlib import Path
import sqlite3

from graphviz import Digraph

# Папка проекта
BASE_DIR = Path(__file__).resolve().parent.parent

# Путь к базе данных
DB_PATH = BASE_DIR / "db" / "materials.sqlite3"

# Путь для сохранения диаграммы
OUTPUT_PATH = BASE_DIR / "docs" / "er_diagram"


def create_er_diagram():
    connection = sqlite3.connect(DB_PATH)

    diagram = Digraph("ER_Diagram", format="pdf")
    diagram.attr(rankdir="LR")
    diagram.attr("node", shape="record", fontsize="10")

    tables = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        AND name NOT LIKE 'sqlite_%'
        ORDER BY name
        """
    ).fetchall()

    for (table_name,) in tables:
        columns = connection.execute(
            f'PRAGMA table_info("{table_name}")'
        ).fetchall()

        foreign_keys = connection.execute(
            f'PRAGMA foreign_key_list("{table_name}")'
        ).fetchall()

        foreign_key_columns = {
            fk[3] for fk in foreign_keys
        }

        fields = []

        for column in columns:
            name = column[1]
            data_type = column[2]
            primary_key = column[5]

            if primary_key:
                name = "PK " + name
            elif name in foreign_key_columns:
                name = "FK " + name

            fields.append(f"{name}: {data_type}")

        label = (
            "{"
            + table_name
            + "|"
            + r"\l".join(fields)
            + r"\l}"
        )

        diagram.node(table_name, label=label)

        for fk in foreign_keys:
            diagram.edge(table_name, fk[2])

    connection.close()

    diagram.render(str(OUTPUT_PATH), cleanup=True)

    print("ER-диаграмма успешно создана!")
    print(OUTPUT_PATH.with_suffix(".pdf"))


if __name__ == "__main__":
    create_er_diagram()
