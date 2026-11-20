"""Script tạo tài khoản Admin cho NightFood (FR-08, 8.7, NFR-03, NFR-10)."""
import os
import sys

# Đảm bảo in UTF-8 trên Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Thêm thư mục backend vào sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.auth import hash_password
from app.db.session import SessionLocal
from app.models.user import User


def create_or_update_admin(username: str, password: str, full_name: str = "Quản Trị Viên NightFood"):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        hashed = hash_password(password)

        if user:
            print(f"[!] Tai khoan '{username}' da ton tai -> Cap nhat mat khau va quyen admin.")
            user.password_hash = hashed
            user.role = "admin"
            user.is_active = True
            user.full_name = full_name
        else:
            user = User(
                username=username,
                password_hash=hashed,
                full_name=full_name,
                role="admin",
                is_active=True,
            )
            db.add(user)

        db.commit()
        print(f"[OK] Tao thanh cong tai khoan Admin:")
        print(f"     Username:  {username}")
        print(f"     Full Name: {full_name}")
        print(f"     Role:      admin")
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Loi tao tai khoan admin: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) >= 3:
        u = sys.argv[1]
        p = sys.argv[2]
        fn = sys.argv[3] if len(sys.argv) > 3 else "Quản Trị Viên"
    else:
        print("=== TAO TAI KHOAN ADMIN NIGHTFOOD ===")
        u = input("Nhap username: ").strip() or "admin"
        p = input("Nhap mat khau: ").strip() or "admin123"
        fn = input("Nhap ho ten: ").strip() or "Quản Trị Viên"

    create_or_update_admin(u, p, fn)
