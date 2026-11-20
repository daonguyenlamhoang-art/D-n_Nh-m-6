// Các hàm tiện ích dùng chung cho NightFood Frontend (NFR-13, Chống XSS)

// Chống XSS (NFR-13): Luôn lọc dữ liệu người dùng / API trước khi chèn vào innerHTML
function escapeHtml(value) {
  if (value === null || value === undefined) return "";
  const div = document.createElement("div");
  div.textContent = String(value);
  return div.innerHTML;
}

// Định dạng tiền tệ VND: 35000 -> "35.000đ"
function formatVND(value) {
  if (isNaN(value)) return "0đ";
  return Number(value).toLocaleString("vi-VN") + "đ";
}

// Alias tương thích với base code CRUD mẫu (items.js)
function formatMoney(value) {
  return formatVND(value);
}

// Định dạng thời gian
function formatDateTime(value) {
  if (!value) return "";
  const d = new Date(value);
  return (
    d.toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" }) +
    " " +
    d.toLocaleDateString("vi-VN", { day: "2-digit", month: "2-digit", year: "numeric" })
  );
}

// Hiển thị thông báo Toast góc dưới màn hình: type = "success" | "error" | "warning"
function showToast(message, type = "success") {
  let container = document.getElementById("toast-container");
  if (!container) {
    container = document.createElement("div");
    container.id = "toast-container";
    container.className = "toast-container";
    document.body.appendChild(container);
  }

  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(30px)";
    toast.style.transition = "all 0.3s ease";
    setTimeout(() => toast.remove(), 300);
  }, 3200);
}
