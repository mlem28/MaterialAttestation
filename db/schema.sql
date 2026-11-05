
PRAGMA foreign_keys = ON;

-- Таблица типов материалов
CREATE TABLE IF NOT EXISTS material_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

-- Таблица материалов
CREATE TABLE IF NOT EXISTS materials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    type_id INTEGER NOT NULL,
    image TEXT,
    price REAL NOT NULL DEFAULT 0 CHECK (price >= 0),
    stock INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
    min_stock INTEGER NOT NULL DEFAULT 0 CHECK (min_stock >= 0),
    pack_size INTEGER NOT NULL DEFAULT 1 CHECK (pack_size > 0),
    unit TEXT NOT NULL DEFAULT 'шт.',
    description TEXT NOT NULL DEFAULT '',

    FOREIGN KEY (type_id)
        REFERENCES material_types(id)
);

-- Таблица поставщиков
CREATE TABLE IF NOT EXISTS suppliers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    legal_type TEXT,
    tax_id TEXT,
    quality_rating INTEGER,
    start_date TEXT
);

-- Связь материалов и поставщиков
CREATE TABLE IF NOT EXISTS material_suppliers (
    material_id INTEGER NOT NULL,
    supplier_id INTEGER NOT NULL,

    PRIMARY KEY (material_id, supplier_id),

    FOREIGN KEY (material_id)
        REFERENCES materials(id) ON DELETE CASCADE,

    FOREIGN KEY (supplier_id)
        REFERENCES suppliers(id) ON DELETE CASCADE
);

-- История изменения остатков
CREATE TABLE IF NOT EXISTS stock_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    material_id INTEGER NOT NULL,
    old_stock INTEGER NOT NULL,
    new_stock INTEGER NOT NULL,
    changed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (material_id)
        REFERENCES materials(id) ON DELETE CASCADE
);

-- Продукция предприятия
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
);

-- Материалы, используемые в продукции
CREATE TABLE IF NOT EXISTS product_materials (
    product_id INTEGER NOT NULL,
    material_id INTEGER NOT NULL,
    quantity REAL NOT NULL CHECK (quantity > 0),

    PRIMARY KEY (product_id, material_id),

    FOREIGN KEY (product_id)
        REFERENCES products(id),

    FOREIGN KEY (material_id)
        REFERENCES materials(id) ON DELETE RESTRICT
);
