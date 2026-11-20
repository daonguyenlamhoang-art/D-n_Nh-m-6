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

          <div class="nav-actions" style="display:flex; align-items:center; gap:8px;">
            <a href="${root}cart.html" class="cart-btn" id="nav-cart-btn">
              <span>🛒 Giỏ hàng</span>
              <span class="cart-badge" id="nav-cart-badge">0</span>
            </a>
            <button type="button" class="btn btn-secondary" id="btn-open-cart-drawer" style="padding:7px 11px; border-radius:999px; font-size:0.85rem;" title="Xem nhanh ngăn kéo giỏ hàng">
              ⚡
            </button>
          </div>
        </div>
      </nav>

      <!-- Ngăn kéo giỏ hàng trượt trên mobile / Xem nhanh (T3D2887) -->
      <div id="mobile-cart-drawer-overlay" class="cart-drawer-overlay"></div>
      <aside id="mobile-cart-drawer" class="cart-drawer">
        <div style="padding:16px 20px; border-bottom:1px solid var(--border-color); display:flex; justify-content:space-between; align-items:center;">
          <h3 style="font-size:1.1rem; font-weight:800;">🛒 Giỏ Hàng Nhanh</h3>
          <button type="button" id="btn-close-cart-drawer" class="modal-close-btn">&times;</button>
        </div>
        <div id="mobile-cart-drawer-body" style="padding:16px; flex:1; overflow-y:auto;"></div>
        <div style="padding:16px 20px; border-top:1px solid var(--border-color); display:flex; gap:10px;">
          <a href="${root}cart.html" class="btn btn-secondary" style="flex:1;">Mở Giỏ Hàng</a>
          <a href="${root}checkout.html" class="btn btn-primary" style="flex:1;">Thanh Toán</a>
        </div>
      </aside>
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
  renderMobileCartDrawer();
}

function renderMobileCartDrawer() {
  const openBtn = document.getElementById("btn-open-cart-drawer");
  const closeBtn = document.getElementById("btn-close-cart-drawer");
  const overlay = document.getElementById("mobile-cart-drawer-overlay");
  const drawer = document.getElementById("mobile-cart-drawer");
  const bodyEl = document.getElementById("mobile-cart-drawer-body");

  if (openBtn && drawer && overlay && !openBtn.dataset.bound) {
    openBtn.dataset.bound = "1";
    const closeFn = () => {
      drawer.classList.remove("active");
      overlay.classList.remove("active");
    };
    openBtn.addEventListener("click", () => {
      renderMobileCartDrawer();
      drawer.classList.add("active");
      overlay.classList.add("active");
    });
    if (closeBtn) closeBtn.addEventListener("click", closeFn);
    overlay.addEventListener("click", closeFn);
  }

  if (!bodyEl || typeof CartStorage === "undefined") return;
  const items = CartStorage.getItems();
  if (!items.length) {
    bodyEl.innerHTML = `<div style="text-align:center; padding:40px 10px; color:var(--text-dim);">Giỏ hàng đang trống.</div>`;
    return;
  }

  bodyEl.innerHTML = items.map((it, idx) => `
    <div style="padding:10px 0; border-bottom:1px solid var(--border-subtle); display:flex; justify-content:space-between; align-items:center; gap:8px;">
      <div>
        <div style="font-weight:700; font-size:0.9rem;">Món #${it.dish_id} (SL: ${it.quantity})</div>
        ${it.option_name ? `<div style="font-size:0.78rem; color:var(--accent-primary);">+ ${escapeHtml(it.option_name)}</div>` : ''}
        ${it.note ? `<div style="font-size:0.75rem; color:var(--text-dim);">📝 ${escapeHtml(it.note)}</div>` : ''}
      </div>
      <div class="qty-control">
        <button class="qty-btn" onclick="CartStorage.updateQuantityByIndex(${idx}, ${it.quantity - 1})">-</button>
        <div class="qty-val">${it.quantity}</div>
        <button class="qty-btn" onclick="CartStorage.updateQuantityByIndex(${idx}, ${it.quantity + 1})">+</button>
      </div>
    </div>
  `).join("");
}
