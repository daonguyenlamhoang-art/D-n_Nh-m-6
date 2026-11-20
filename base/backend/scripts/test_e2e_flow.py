"""Kịch bản kiểm thử luồng xuyên suốt toàn hệ thống NightFood (E2E Integration Test - T3D1C40..T3D1C48)."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app


def run_e2e_flow():
    client = TestClient(app)

    # 1. Kiểm tra kết nối MySQL & Menu khách (6 danh mục, 30 món)
    h = client.get("/api/health")
    assert h.status_code == 200 and h.json()["database"] == "connected"

    menu = client.get("/api/dishes/menu")
    assert menu.status_code == 200
    assert len(menu.json()["categories"]) >= 6

    # 2. Tìm kiếm & xem chi tiết món kèm nhóm tuỳ chọn
    srch = client.get("/api/dishes/search?q=mi&sort_by=price_asc")
    assert srch.status_code == 200 and srch.json()["total"] >= 1
    detail = client.get("/api/dishes/1")
    assert detail.status_code == 200 and len(detail.json()["option_groups"]) >= 1

    # 3. Thêm vào giỏ hàng & tính tiền tại server (khu vực + mã giảm giá)
    gt = "e2e_flow_token"
    client.delete("/api/cart", headers={"X-Guest-Token": gt})
    add_c = client.post(
        "/api/cart/items",
        json={"dish_id": 1, "quantity": 2, "selected_option_ids": [2, 3], "note": "Ít cay"},
        headers={"X-Guest-Token": gt},
    )
    assert add_c.status_code == 201
    calc = client.get("/api/cart?area=Thanh%20Xu%C3%A2n&voucher_code=demkhuya10", headers={"X-Guest-Token": gt})
    assert calc.status_code == 200 and calc.json()["discount_amount"] > 0

    # 4. Đặt món trong transaction
    ord_res = client.post(
        "/api/orders",
        json={
            "customer_name": "Khách Hàng E2E",
            "phone": "0912345678",
            "address": "69 Vũ Trọng Phụng, Thanh Xuân, Hà Nội",
            "area": "Thanh Xuân",
            "desired_delivery_time": "22:15",
            "payment_method": "COD",
            "voucher_code": "demkhuya10",
            "guest_token": gt,
            "items": [{"dish_id": 1, "quantity": 2, "selected_option_ids": [2, 3], "note": "Ít cay"}],
        },
    )
    assert ord_res.status_code == 201
    code = ord_res.json()["order_code"]
    oid = ord_res.json()["id"]

    # 5. Nhân viên xử lý đơn qua các bước -> Hoàn thành
    login = client.post("/api/admin/login", json={"username": "admin", "password": "admin123"})
    assert login.status_code == 200
    h_adm = {"Authorization": f"Bearer {login.json()['token']}"}

    for st in ["confirmed", "preparing", "delivering", "completed"]:
        st_res = client.patch(f"/api/admin/orders/{oid}/status", json={"status": st}, headers=h_adm)
        assert st_res.status_code == 200

    # 6. Khách theo dõi đơn, gửi đánh giá & chat hỗ trợ
    trk = client.get(f"/api/orders/{code}/track?guest_token={gt}")
    assert trk.status_code == 200 and trk.json()["status"] == "completed"

    rev = client.post(
        "/api/reviews",
        json={"order_code": code, "guest_token": gt, "dish_id": 1, "rating": 5, "comment": "Mì trộn tuyệt vời!"},
    )
    assert rev.status_code == 201

    msg = client.post(
        "/api/chat/messages",
        json={"guest_token": gt, "customer_name": "Khách Hàng E2E", "message": "Cảm ơn quán nhé!"},
    )
    assert msg.status_code == 201

    # 7. Dashboard Admin
    dash = client.get("/api/admin/dashboard/analytics?group_by=day", headers=h_adm)
    assert dash.status_code == 200 and dash.json()["total_revenue"] > 0

    print(f"[E2E PASS] Full system flow verified! Order={code}, TotalRevenue={dash.json()['total_revenue']}")


if __name__ == "__main__":
    run_e2e_flow()
