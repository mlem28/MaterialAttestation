import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from database import get_connection

class MaterialsApp:
    def __init__(self, root):
        self.root = root
        self.page_size = 20
        self.current_page = 1
        self.total_pages = 1
        self.root.title("Учёт материалов предприятия")
        self.root.geometry("1100x650")
        self.root.minsize(850, 500)

        # Заголовок приложения
        title = ttk.Label(
            root,
            text="Учёт материалов предприятия",
            font=("Arial", 20, "bold")
        )
        title.pack(pady=15)

        # Панель поиска
        search_frame = ttk.Frame(root)
        search_frame.pack(fill="x", padx=20, pady=10)

        ttk.Label(
            search_frame,
            text="Поиск материала:"
        ).pack(side="left")

        self.search_var = tk.StringVar()

        search_entry = ttk.Entry(
            search_frame,
            textvariable=self.search_var,
            width=40
        )
        search_entry.pack(side="left", padx=10)

        ttk.Button(
            search_frame,
            text="Найти",
            command=self.search_materials
        ).pack(side="left")

        ttk.Button(
            search_frame,
            text="Сбросить",
            command=self.reset_search
        ).pack(side="left", padx=5)

        # Таблица материалов
        columns = (
            "id",
            "name",
            "price",
            "stock",
            "unit"
        )

        self.table = ttk.Treeview(
            root,
            columns=columns,
            show="headings"
        )

        headings = {
            "id": "ID",
            "name": "Наименование",
            "price": "Цена",
            "stock": "На складе",
            "unit": "Ед. изм."
        }

        for column, heading in headings.items():
            self.table.heading(column, text=heading)

        self.table.column("id", width=60)
        self.table.column("name", width=350)
        self.table.column("price", width=120)
        self.table.column("stock", width=120)
        self.table.column("unit", width=100)

        self.table.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=10
        )

        # Нижняя панель
        bottom_frame = ttk.Frame(root)
        bottom_frame.pack(fill="x", padx=20, pady=10)

        ttk.Button(
            bottom_frame,
            text="Обновить",
            command=self.load_materials
        ).pack(side="left")

                # Кнопка добавления материала
        ttk.Button(
            bottom_frame,
            text="Добавить",
            command=self.add_material
        ).pack(side="left", padx=5)

        # Кнопка изменения материала
        ttk.Button(
            bottom_frame,
            text="Изменить",
            command=self.edit_material
        ).pack(side="left", padx=5)

        # Кнопка удаления материала
        ttk.Button(
            bottom_frame,
            text="Удалить",
            command=self.delete_material
        ).pack(side="left", padx=5)


        # Кнопки переключения страниц
        self.prev_button = ttk.Button(
            bottom_frame,
            text="Назад",
            command=self.previous_page
        )
        self.prev_button.pack(side="left", padx=5)

        self.next_button = ttk.Button(
            bottom_frame,
            text="Вперёд",
            command=self.next_page
        )
        self.next_button.pack(side="left", padx=5)

        self.page_label = ttk.Label(
            bottom_frame,
            text="Страница 1 из 1"
        )
        self.page_label.pack(side="left", padx=10)


        self.status_label = ttk.Label(
            bottom_frame,
            text="Материалы загружаются..."
        )
        self.status_label.pack(side="right")

        self.load_materials()

    
    def reset_search(self):
        """Сбрасывает поиск и возвращает первую страницу."""
        self.search_var.set("")
        self.current_page = 1
        self.load_materials()

    def search_materials(self):
        """Ищет материалы с первой страницы."""
        self.current_page = 1
        self.load_materials()

    
    def load_materials(self):
        """Загружает материалы с учётом поиска и пагинации."""
        search = self.search_var.get().strip()

        try:
            with get_connection() as connection:
                total = connection.execute(
                    """
                    SELECT COUNT(*)
                    FROM materials
                    WHERE name LIKE ?
                    """,
                    (f"%{search}%",)
                ).fetchone()[0]

                self.total_pages = max(
                    1,
                    (total + self.page_size - 1) // self.page_size
                )

                self.current_page = min(
                    max(1, self.current_page),
                    self.total_pages
                )

                offset = (self.current_page - 1) * self.page_size

                rows = connection.execute(
                    """
                    SELECT id, name, price, stock, unit
                    FROM materials
                    WHERE name LIKE ?
                    ORDER BY name, id
                    LIMIT ? OFFSET ?
                    """,
                    (f"%{search}%", self.page_size, offset)
                ).fetchall()

            for item in self.table.get_children():
                self.table.delete(item)

            for row in rows:
                self.table.insert("", "end", values=row)

            self.page_label.config(
                text=f"Страница {self.current_page} из {self.total_pages}"
            )

            self.prev_button.config(
                state="normal" if self.current_page > 1 else "disabled"
            )

            self.next_button.config(
                state="normal" if self.current_page < self.total_pages
                else "disabled"
            )

            self.status_label.config(
                text=f"Показано: {len(rows)} из {total}"
            )

        except Exception as error:
            messagebox.showerror(
                "Ошибка базы данных",
                str(error)
            )

    def previous_page(self):
        """Переходит на предыдущую страницу."""
        if self.current_page > 1:
            self.current_page -= 1
            self.load_materials()

    def next_page(self):
        """Переходит на следующую страницу."""
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.load_materials()


    def reset_search(self):
        self.search_var.set("")
        self.load_materials()

    def add_material(self):
        window = tk.Toplevel(self.root)
        window.title("Добавление материала")
        window.geometry("420x330")
        window.transient(self.root)
        window.grab_set()
        # Создаём поля для ввода материала
        fields = [
            ("Наименование", ""),
            ("Цена", "0"),
            ("Количество на складе", "0"),
            ("Единица измерения", "шт")
        ]

        # Загружаем типы материалов из базы данных
        with get_connection() as connection:
            material_types = connection.execute(
                "SELECT id, name FROM material_types ORDER BY name"
            ).fetchall()

        # Создаем список названий типов
        type_names = [item[1] for item in material_types]

        # Надпись для выбора типа
        ttk.Label(
            window,
            text="Тип материала:"
        ).grid(
            row=0,
            column=0,
            padx=10,
            pady=5,
            sticky="w"
        )

        # Выпадающий список типов материалов
        type_combo = ttk.Combobox(
            window,
            values=type_names,
            state="readonly",
            width=25
        )

        type_combo.grid(
            row=0,
            column=1,
            padx=10,
            pady=5
        )

        if type_names:
            type_combo.current(0)
        entries = {}

        for row, (label, default) in enumerate(fields, start=1):
            ttk.Label(
                window,
                text=label
            ).grid(
                row=row,
                column=0,
                padx=10,
                pady=5,
                sticky="w"
            )

            entry = ttk.Entry(window, width=25)
            entry.insert(0, default)
            entry.grid(
                row=row,
                column=1,
                padx=10,
                pady=10
            )

            entries[label] = entry

        def save_material():
            name = entries["Наименование"].get().strip()
            price_text = entries["Цена"].get().strip()
            stock_text = entries["Количество на складе"].get().strip()
            unit = entries["Единица измерения"].get().strip()
            # Проверяем выбранный тип материала
            selected_index = type_combo.current()

            if selected_index == -1:
                messagebox.showwarning(
                    "Ошибка",
                    "Выберите тип материала.",
                    parent=window
                )
                return

            type_id = material_types[selected_index][0]
            if not name or not unit:
                messagebox.showwarning(
                    "Ошибка",
                    "Заполни наименование и единицу измерения.",
                    parent=window
                )
                return

            try:
                price = float(price_text.replace(",", "."))
                stock = int(stock_text)

                if price < 0 or stock < 0:
                    raise ValueError

            except ValueError:
                messagebox.showerror(
                    "Ошибка",
                    "Цена и количество должны быть неотрицательными числами.",
                    parent=window
                )
                return

            try:
                with get_connection() as connection:
                    connection.execute(
                    """
                    INSERT INTO materials (name, type_id, price, stock, unit)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (name, type_id, price, stock, unit)
                )
                    connection.commit()
                messagebox.showinfo(
                    "Успешно",
                    "Материал добавлен в базу данных!",
                    parent=window
                )

                window.destroy()
                self.load_materials()

            except Exception as error:
                messagebox.showerror(
                    "Ошибка сохранения",
                    str(error),
                    parent=window
                )

        ttk.Button(
            window,
            text="Проверить данные",
            command=save_material
        ).grid(
            row=len(fields),
            column=0,
            columnspan=2,
            pady=20
        )

       
    
    def edit_material(self):
        """Редактирование выбранного материала."""

        selected = self.table.selection()

        if not selected:
            messagebox.showwarning(
                "Внимание",
                "Сначала выберите материал в таблице."
            )
            return

        values = self.table.item(selected[0], "values")
        material_id = int(values[0])

        window = tk.Toplevel(self.root)
        window.title("Изменение материала")
        window.geometry("400x300")
        window.transient(self.root)
        window.grab_set()

        fields = [
            ("Наименование", values[1]),
            ("Цена", values[2]),
            ("Количество на складе", values[3]),
            ("Единица измерения", values[4])
        ]

        entries = {}

        for row, (label, value) in enumerate(fields):
            ttk.Label(
                window,
                text=label
            ).grid(row=row, column=0, padx=10, pady=10)

            entry = ttk.Entry(window, width=25)
            entry.insert(0, value)
            entry.grid(row=row, column=1, padx=10, pady=10)

            entries[label] = entry

        def save_changes():
            name = entries["Наименование"].get().strip()
            price_text = entries["Цена"].get().strip()
            stock_text = entries["Количество на складе"].get().strip()
            unit = entries["Единица измерения"].get().strip()

            if not name or not unit:
                messagebox.showwarning(
                    "Ошибка",
                    "Заполните наименование и единицу измерения.",
                    parent=window
                )
                return

            try:
                price = float(price_text.replace(",", "."))
                stock = int(stock_text)

                if not 0 <= price < float("inf") or stock < 0:
                    raise ValueError

            except ValueError:
                messagebox.showerror(
                    "Ошибка",
                    "Цена и количество должны быть корректными неотрицательными числами.",
                    parent=window
                )
                return

            try:
                with get_connection() as connection:
                    cursor = connection.execute(
                        """
                        UPDATE materials
                        SET name = ?, price = ?, stock = ?, unit = ?
                        WHERE id = ?
                        """,
                        (name, price, stock, unit, material_id)
                    )

                    if cursor.rowcount != 1:
                        raise ValueError("Материал не найден в базе данных.")

                    connection.commit()

                messagebox.showinfo(
                    "Успешно",
                    "Материал успешно изменён!",
                    parent=window
                )

                window.destroy()
                self.load_materials()

            except Exception as error:
                messagebox.showerror(
                    "Ошибка сохранения",
                    str(error),
                    parent=window
                )

        ttk.Button(
            window,
            text="Сохранить изменения",
            command=save_changes
        ).grid(
            row=4,
            column=0,
            columnspan=2,
            pady=20
        )




    
    def delete_material(self):
        """Удаляет выбранный материал после подтверждения."""

        selected = self.table.selection()

        if not selected:
            messagebox.showwarning(
                "Внимание",
                "Сначала выберите материал для удаления."
            )
            return

        values = self.table.item(selected[0], "values")

        material_id = int(values[0])
        material_name = values[1]

        confirm = messagebox.askyesno(
            "Подтверждение удаления",
            f"Вы действительно хотите удалить материал:\n\n"
            f"{material_name} (ID: {material_id})?"
        )

        if not confirm:
            return

        try:
            with get_connection() as connection:
                cursor = connection.execute(
                    "DELETE FROM materials WHERE id = ?",
                    (material_id,)
                )

                if cursor.rowcount != 1:
                    raise ValueError("Материал не найден в базе данных.")

                connection.commit()

            messagebox.showinfo(
                "Успешно",
                "Материал успешно удалён!"
            )

            self.load_materials()

        except Exception as error:
            messagebox.showerror(
                "Ошибка удаления",
                str(error)
            )

if __name__ == "__main__":
    root = tk.Tk()
    app = MaterialsApp(root)
    root.mainloop()
