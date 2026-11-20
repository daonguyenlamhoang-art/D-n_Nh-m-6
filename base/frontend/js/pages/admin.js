// Module dùng chung cho các trang Admin NightFood (FR-08, FR-15, NFR-04)

async function checkAdminAuth() {
  try {
    const adminUser = await api.get("/admin/me");
    const userDisplay = document.getElementById("admin-display-name");
    if (userDisplay) {
      userDisplay.textContent = adminUser.full_name || adminUser.username || "Admin";
    }
    return adminUser;
  } catch (err) {
    console.warn("Phiên Admin không hợp lệ, chuyển về login:", err);
    localStorage.removeItem("nightfood_admin_token");
    localStorage.removeItem("nightfood_admin_user");
    window.location.href = "login.html";
    return null;
  }
}

async function handleAdminLogout() {
  try {
    await api.post("/admin/logout");
  } catch (e) {
    console.warn("Lỗi khi gọi logout API:", e);
  } finally {
    localStorage.removeItem("nightfood_admin_token");
    localStorage.removeItem("nightfood_admin_user");
    window.location.href = "login.html";
  }
}

// Bật/tắt mở cửa cưỡng bức (STORE_FORCE_OPEN) để phục vụ kiểm thử / chấm điểm đồ án (FR-14, TC-39)
async function toggleStoreStatus() {
  try {
    const res = await api.post("/store/toggle-force-open");
    showToast(`Trạng thái quán: ${res.status_text}`, res.is_open ? "success" : "warning");
    const statusBtn = document.getElementById("btn-store-toggle");
    if (statusBtn) {
      statusBtn.textContent = res.force_open ? "⚡ Đang Ép Mở (Click để tắt)" : "🌙 Tuân theo giờ thật (18h-2h)";
      statusBtn.className = res.force_open ? "btn btn-primary" : "btn btn-secondary";
    }
  } catch (err) {
    showToast("Không thể thay đổi trạng thái quán: " + err.message, "error");
  }
}
