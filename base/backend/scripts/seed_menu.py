"""Script nâng cấp schema và seed 6 danh mục + 30 món ăn kèm tuỳ chọn (T3D1F81)."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text
from app.db.session import SessionLocal, engine
from app.models.category import Category
from app.models.dish import Dish, DishOption
from scripts.create_admin import ensure_admin


def apply_schema_and_seed():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    schema_path = os.path.join(base_dir, "database", "schema.sql")
    sample_path = os.path.join(base_dir, "database", "sample_data.sql")

    with engine.begin() as conn:
        for sql_file in [schema_path, sample_path]:
            with open(sql_file, "r", encoding="utf-8") as f:
                content = f.read()
            for stmt in content.split(";"):
                lines = [line for line in stmt.splitlines() if not line.strip().startswith("--")]
                clean_stmt = "\n".join(lines).strip()
                if clean_stmt:
                    conn.execute(text(clean_stmt))

    ensure_admin("admin", "admin123", "Quản Trị Viên NightFood")

    db = SessionLocal()
    try:
        cat_count = db.query(Category).count()
        dish_count = db.query(Dish).count()
        opt_count = db.query(DishOption).count()
        print(f"[SEED OK] Categories: {cat_count} | Dishes: {dish_count} | Options: {opt_count}")
        assert cat_count == 6, f"Expected 6 categories, got {cat_count}"
        assert dish_count == 30, f"Expected 30 dishes, got {dish_count}"
    finally:
        db.close()


if __name__ == "__main__":
    apply_schema_and_seed()
