"""Script khởi tạo tài khoản Admin mặc định cho NightFood.
Chạy: python scripts/create_admin.py [username] [password] [full_name]
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text
from app.core.auth import hash_password
from app.db.session import SessionLocal, engine, Base
import app.models  # noqa: F401
from app.models.user import User


def init_db_if_needed():
    """Đảm bảo cấu trúc bảng trong MySQL khớp với schema.sql và sample_data.sql."""
    with engine.connect() as conn:
        try:
            conn.execute(text("SELECT username FROM users LIMIT 1"))
            return
        except Exception:
            print("[DB] Updating schema from database/schema.sql and database/sample_data.sql...")

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    schema_path = os.path.join(base_dir, "database", "schema.sql")
    sample_path = os.path.join(base_dir, "database", "sample_data.sql")

    with engine.begin() as conn:
        for sql_file in [schema_path, sample_path]:
            if os.path.exists(sql_file):
                with open(sql_file, "r", encoding="utf-8") as f:
                    content = f.read()
                for stmt in content.split(";"):
                    lines = [line for line in stmt.splitlines() if not line.strip().startswith("--")]
                    clean_stmt = "\n".join(lines).strip()
                    if clean_stmt:
                        conn.execute(text(clean_stmt))
    Base.metadata.create_all(bind=engine)


def ensure_admin(username: str = "admin", password: str = "admin123", full_name: str = "Quản Trị Viên NightFood"):
    init_db_if_needed()
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user:
            user.password_hash = hash_password(password)
            user.role = "admin"
            user.is_active = True
            user.full_name = full_name
        else:
            user = User(
                username=username,
                password_hash=hash_password(password),
                full_name=full_name,
                phone="0988888999",
                role="admin",
                is_active=True,
            )
            db.add(user)
        db.commit()
        print(f"[OK] Admin user '{username}' is ready.")
    finally:
        db.close()


if __name__ == "__main__":
    u = sys.argv[1] if len(sys.argv) > 1 else "admin"
    p = sys.argv[2] if len(sys.argv) > 2 else "admin123"
    n = sys.argv[3] if len(sys.argv) > 3 else "Quản Trị Viên NightFood"
    ensure_admin(u, p, n)
