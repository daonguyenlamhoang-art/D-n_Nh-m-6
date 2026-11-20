// Cấu hình NightFood Frontend
const CONFIG = {
  APP_NAME: "NightFood",
  // Tự động nhận diện nếu chạy trực tiếp qua FastAPI (:8000) hay Live Server (:5500)
  API_BASE_URL: (window.location.port === "8000" || window.location.pathname.startsWith("/admin"))
    ? "/api"
    : (window.location.origin.includes("127.0.0.1") || window.location.origin.includes("localhost"))
      ? "http://127.0.0.1:8000/api"
      : "/api",
};
