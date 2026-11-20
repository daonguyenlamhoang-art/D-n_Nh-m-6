// Module gọi REST API dùng chung cho toàn bộ dự án NightFood
class ApiError extends Error {
  constructor(message, status, data, code = "") {
    super(message);
    this.status = status;
    this.data = data;
    this.code = code;
  }
}

const http = axios.create({
  baseURL: CONFIG.API_BASE_URL,
  timeout: 10000,
  withCredentials: true, // Gửi kèm Cookie HttpOnly cho phiên Admin
  headers: { "Content-Type": "application/json" },
});

// Thêm token nếu có lưu trong localStorage (hỗ trợ cả header lẫn cookie)
http.interceptors.request.use((config) => {
  const token = localStorage.getItem("nightfood_admin_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Xử lý chuẩn hóa lỗi từ backend (SRS 8.1: {"error": {"code": "...", "message": "...", "details": ...}})
http.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      const { status, data } = error.response;
      let msg = `Lỗi hệ thống (${status})`;
      let code = "";

      if (data && data.error) {
        msg = data.error.message || msg;
        code = data.error.code || "";
      } else if (data && typeof data.detail === "string") {
        msg = data.detail;
      } else if (data && typeof data.detail === "object") {
        msg = data.detail.message || JSON.stringify(data.detail);
        code = data.detail.code || "";
      }

      // Xử lý tự động chuyển về trang đăng nhập nếu là trang Admin và gặp 401
      if (status === 401 && window.location.pathname.includes("/admin/") && !window.location.pathname.includes("login.html")) {
        localStorage.removeItem("nightfood_admin_token");
        localStorage.removeItem("nightfood_admin_user");
        window.location.href = "login.html";
      }

      return Promise.reject(new ApiError(msg, status, data, code));
    }
    return Promise.reject(
      new ApiError("Không thể kết nối đến máy chủ. Vui lòng kiểm tra backend đã chạy chưa.", 0, null)
    );
  }
);

const api = {
  get: (url, params) => http.get(url, { params }).then((res) => res.data),
  post: (url, body) => http.post(url, body).then((res) => res.data),
  put: (url, body) => http.put(url, body).then((res) => res.data),
  patch: (url, body) => http.patch(url, body).then((res) => res.data),
  delete: (url) => http.delete(url).then((res) => res.data),
};
