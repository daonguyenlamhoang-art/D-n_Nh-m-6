// Khung giao diện dùng chung (Header, Footer, Trạng thái quán và Badge Giỏ hàng)

document.addEventListener("DOMContentLoaded", () => {
  renderLayout();
  initStoreStatus();
  updateCartBadge();

  window.addEventListener("nightfood_cart_changed", () => {
    updateCartBadge();
  });
});

function getRootPrefix() {
  const bodyRoot = document.body.getAttribute("data-root");
  return bodyRoot !== null ? bodyRoot : "./";
}

function renderLayout() {
  const root = getRootPrefix();
  const currentPath = window.location.pathname;

  const headerEl = document.getElementById("app-header");
  if (headerEl) {
    headerEl.innerHTML = `
      <!-- Thanh trạng thái mở cửa (FR-14) -->
      <div class="store-status-bar">
        <div class="container store-status-content">
          <div style="display:flex; align-items:center; gap:8px;">
            <span class="pulse-dot" id="header-store-dot" style="color:#22c55e;"></span>
            <span id="header-store-text">Đang kiểm tra trạng thái quán...</span>
          </div>
          <div style="display:flex; align-items:center; gap:14px; flex-wrap:wrap;">
            <span>⏰ Giờ mở cửa: <strong>18:00 - 02:00</strong> hằng đêm | 🛵 Giao nhanh trong 20 phút</span>
            <span id="header-mysql-badge" style="padding:2px 10px; border-radius:999px; font-size:0.78rem; font-weight:700; background:rgba(34,197,94,0.15); color:#4ade80; border:1px solid rgba(34,197,94,0.3);">MySQL: connected</span>
          </div>
        </div>
      </div>

      <!-- Thanh điều hướng chính -->
      <nav class="navbar">
        <div class="container nav-container">
          <a href="${root}index.html" class="brand-logo">
            <span class="logo-icon">🌙</span>
            <span>Night<span class="highlight">Food</span></span>
          </a>

          <ul class="nav-links">
            <li><a href="${root}index.html" class="${currentPath.endsWith('index.html') || currentPath === '/' ? 'active' : ''}">Trang chủ</a></li>
            <li><a href="${root}dishes.html" class="${currentPath.endsWith('dishes.html') ? 'active' : ''}">Thực đơn đêm</a></li>
            <li><a href="${root}order-lookup.html" class="${currentPath.endsWith('order-lookup.html') ? 'active' : ''}">Tra cứu đơn</a></li>
            <li><a href="${root}admin/login.html" style="color:var(--text-dim); font-size:0.85rem;">🔒 Quản trị</a></li>
          </ul>

          <div class="nav-actions">
            <a href="${root}cart.html" class="cart-btn" id="nav-cart-btn">
              <span>🛒 Giỏ hàng</span>
              <span class="cart-badge" id="nav-cart-badge">0</span>
            </a>
          </div>
        </div>
      </nav>
    `;
  }

  const footerEl = document.getElementById("app-footer");
  if (footerEl) {
    footerEl.innerHTML = `
      <footer class="footer">
        <div class="container">
          <div class="footer-grid">
            <div class="footer-col">
              <div class="brand-logo" style="margin-bottom:12px;">
                <span class="logo-icon">🌙</span>
                <span>Night<span class="highlight">Food</span></span>
              </div>
              <p>Quán bán đồ ăn đêm trực tuyến chuyên phục vụ các món ăn nóng hổi, combo cú đêm, mì trộn, cháo sườn và đồ nướng thơm lừng từ 18h tối đến 2h sáng.</p>
              <p style="margin-top:10px; color:var(--accent-secondary); font-weight:600;">Hotline đặt món: 0988.888.999</p>
            </div>
            <div class="footer-col">
              <h4>Danh mục nổi bật</h4>
              <p><a href="${root}dishes.html">Combo Cú Đêm</a></p>
              <p><a href="${root}dishes.html">Mì & Cơm rang</a></p>
              <p><a href="${root}dishes.html">Đồ chiên ăn vặt</a></p>
              <p><a href="${root}dishes.html">Đồ nướng mật ong</a></p>
              <p><a href="${root}dishes.html">Trà chanh & Trà đào</a></p>
            </div>
            <div class="footer-col">
              <h4>Hỗ trợ khách hàng</h4>
              <p><a href="${root}order-lookup.html">Tra cứu tiến độ giao hàng</a></p>
              <p>Chính sách thanh toán COD</p>
              <p>Cam kết đồ ăn nóng sốt</p>
              <p>Phản hồi chất lượng món</p>
            </div>
          </div>
          <div class="footer-bottom">
            <p>© 2026 NightFood - Đồ Ăn Đêm Nóng Hổi. Dự án bài tập lớn SRS v1.2 (FastAPI + MySQL + HTML/CSS/JS).</p>
          </div>
        </div>
      </footer>
    `;
  }
}

async function initStoreStatus() {
  const dotEl = document.getElementById("header-store-dot");
  const textEl = document.getElementById("header-store-text");
  if (!textEl) return;

  try {
    api.get("/health").then(h => {
      const mysqlBadge = document.getElementById("header-mysql-badge");
      if (mysqlBadge && h) {
        mysqlBadge.textContent = h.mysql_display || (h.database === "connected" ? "MySQL: connected" : "MySQL: disconnected");
      }
    }).catch(() => {});
    const statusData = await api.get("/store/status");
    if (statusData.is_open) {
      if (dotEl) {
        dotEl.style.color = "#22c55e";
        dotEl.className = "pulse-dot";
      }
      textEl.innerHTML = `<span style="color:#4ade80; font-weight:700;">Đang mở cửa đón khách</span> (${statusData.open_time} - ${statusData.close_time})`;
    } else {
      if (dotEl) {
        dotEl.style.color = "#ef4444";
        dotEl.className = "";
      }
      textEl.innerHTML = `<span style="color:#f87171; font-weight:700;">Đã đóng cửa</span> (Mở cửa từ ${statusData.open_time} đến ${statusData.close_time})`;
    }
  } catch (err) {
    if (textEl) {
      textEl.textContent = "Giờ mở cửa: 18:00 - 02:00 hằng ngày";
    }
  }
}

function updateCartBadge() {
  const badge = document.getElementById("nav-cart-badge");
  if (badge && typeof CartStorage !== "undefined") {
    const count = CartStorage.getTotalCount();
    badge.textContent = count;
    badge.style.display = count > 0 ? "inline-block" : "none";
  }
}
