// Logic Chi tiết món ăn (FR-02, TC-01..02)

let currentDish = null;
let currentQuantity = 1;
let selectedOptionId = null;

document.addEventListener("DOMContentLoaded", async () => {
  const urlParams = new URLSearchParams(window.location.search);
  const dishId = urlParams.get("id");

  if (!dishId) {
    showError("Không tìm thấy mã món ăn trong liên kết");
    return;
  }

  await loadDishDetail(dishId);
});

async function loadDishDetail(id) {
  const container = document.getElementById("dish-detail-container");
  if (!container) return;

  try {
    currentDish = await api.get(`/dishes/${id}`);
    renderDetail(currentDish);
    await loadDishReviewsSection(id);
  } catch (err) {
    showError(err.message || "Không thể tải thông tin món ăn");
  }
}

function showError(msg) {
  const container = document.getElementById("dish-detail-container");
  if (container) {
    container.innerHTML = `
      <div style="text-align:center; padding: 60px 20px;">
        <div style="font-size:3rem; margin-bottom:12px;">⚠️</div>
        <h2 style="color:var(--danger); margin-bottom:8px;">Lỗi tải món ăn</h2>
        <p style="color:var(--text-muted); margin-bottom:20px;">${escapeHtml(msg)}</p>
        <a href="dishes.html" class="btn btn-primary">Quay lại danh sách thực đơn</a>
      </div>
    `;
  }
}

function renderDetail(dish) {
  const container = document.getElementById("dish-detail-container");
  const defaultImg = "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=500&auto=format&fit=crop&q=60";
  const imgUrl = dish.image_url ? escapeHtml(dish.image_url) : defaultImg;
  const isAvailable = dish.is_available;

  const optionsHtml = (dish.options && dish.options.length > 0)
    ? `
      <div style="margin-top:20px; padding-top:16px; border-top:1px solid var(--border-color);">
        <label class="form-label">Tùy chọn thêm:</label>
        <div style="display:flex; flex-direction:column; gap:8px;">
          <label style="display:flex; align-items:center; gap:8px; cursor:pointer; color:var(--text-muted); font-size:0.92rem;">
            <input type="radio" name="dish-option" value="" checked>
            <span>Món tiêu chuẩn (không thêm)</span>
          </label>
          ${dish.options.map(opt => `
            <label style="display:flex; align-items:center; gap:8px; cursor:pointer; color:var(--text-main); font-size:0.92rem;">
              <input type="radio" name="dish-option" value="${opt.id}" data-price="${opt.extra_price}">
              <span>${escapeHtml(opt.option_name)} (+${formatVND(opt.extra_price)})</span>
            </label>
          `).join("")}
        </div>
      </div>
    `
    : "";

  container.innerHTML = `
    <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap:36px; align-items:center;">
      <div style="border-radius:var(--radius-lg); overflow:hidden; border:1px solid var(--border-color); background:#000;">
        <img src="${imgUrl}" alt="${escapeHtml(dish.name)}" style="width:100%; max-height:420px; object-fit:cover; display:block;" onerror="this.src='${defaultImg}'">
      </div>

      <div>
        <div style="display:flex; align-items:center; gap:10px; margin-bottom:10px;">
          <span class="badge-tag" style="background-color:rgba(249,115,22,0.15); color:var(--accent-primary); border:1px solid rgba(249,115,22,0.3); padding:4px 12px; border-radius:999px; font-size:0.82rem; font-weight:600;">
            ${escapeHtml(dish.category_name || 'Đồ ăn đêm')}
          </span>
          <span style="font-size:0.85rem; font-weight:700; color:${isAvailable ? '#4ade80' : '#f87171'};">
            ${isAvailable ? '● Đang có sẵn' : '● Tạm hết hàng'}
          </span>
        </div>

        <h1 style="font-size:2rem; font-weight:800; color:var(--text-main); margin-bottom:12px; line-height:1.25;">
          ${escapeHtml(dish.name)}
        </h1>

        <div style="font-size:1.8rem; font-weight:800; color:var(--accent-secondary); margin-bottom:16px;">
          ${formatVND(dish.price)}
        </div>

        <p style="color:var(--text-muted); font-size:1rem; line-height:1.6; margin-bottom:20px;">
          ${escapeHtml(dish.description || 'Món ăn đêm được chế biến nóng sốt ngay sau khi nhận đơn, bảo đảm giữ nguyên độ giòn và hương vị đậm đà.')}
        </p>

        ${optionsHtml}

        <div style="margin-top:24px; padding-top:20px; border-top:1px solid var(--border-color); display:flex; align-items:center; gap:16px; flex-wrap:wrap;">
          <div>
            <label class="form-label" style="margin-bottom:4px;">Số lượng:</label>
            <div class="qty-control">
              <button class="qty-btn" id="btn-decrease">-</button>
              <div class="qty-val" id="qty-display">1</div>
              <button class="qty-btn" id="btn-increase">+</button>
            </div>
          </div>

          <div style="flex-grow:1; display:flex; align-items:flex-end;">
            <button 
              id="btn-add-cart-detail" 
              class="btn btn-primary" 
              style="width:100%; padding:12px 24px; font-size:1.05rem;" 
              ${!isAvailable ? 'disabled' : ''}>
              🛒 ${isAvailable ? 'Thêm vào giỏ hàng' : 'Món hiện đang hết'}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Khu vực Đánh giá món ăn (T3D2D99) -->
    <div id="dish-reviews-section" style="margin-top:36px; padding-top:24px; border-top:1px solid var(--border-color);">
      <h3 style="font-size:1.25rem; font-weight:700; margin-bottom:14px;">⭐ Đánh Giá Từ Khách Hàng</h3>
      <div id="dish-reviews-list" style="color:var(--text-dim);">Đang tải đánh giá...</div>
    </div>
  `;

  // Gắn sự kiện tăng/giảm số lượng
  const decBtn = document.getElementById("btn-decrease");
  const incBtn = document.getElementById("btn-increase");
  const qtyDisplay = document.getElementById("qty-display");
  const addBtn = document.getElementById("btn-add-cart-detail");

  if (decBtn && incBtn && qtyDisplay) {
    decBtn.addEventListener("click", () => {
      if (currentQuantity > 1) {
        currentQuantity--;
        qtyDisplay.textContent = currentQuantity;
      }
    });

    incBtn.addEventListener("click", () => {
      if (currentQuantity < 99) {
        currentQuantity++;
        qtyDisplay.textContent = currentQuantity;
      } else {
        showToast("Số lượng mỗi món tối đa là 99", "warning");
      }
    });
  }

  // Gắn sự kiện chọn option
  const optionRadios = container.querySelectorAll('input[name="dish-option"]');
  optionRadios.forEach(radio => {
    radio.addEventListener("change", (e) => {
      selectedOptionId = e.target.value ? parseInt(e.target.value) : null;
    });
  });

  // Gắn sự kiện thêm vào giỏ
  if (addBtn && isAvailable) {
    addBtn.addEventListener("click", () => {
      CartStorage.addItem(dish.id, currentQuantity, selectedOptionId);
    });
  }
}

async function loadDishReviewsSection(dishId) {
  const listEl = document.getElementById("dish-reviews-list");
  if (!listEl) return;
  try {
    const res = await api.get(`/dishes/${dishId}/reviews`);
    const items = res.items || [];
    if (items.length === 0) {
      listEl.innerHTML = `<div style="padding:16px; background:var(--bg-main); border-radius:var(--radius-sm); color:var(--text-dim);">Chưa có đánh giá nào cho món này. Hãy đặt món và là người đầu tiên đánh giá nhé!</div>`;
      return;
    }
    listEl.innerHTML = `
      <div style="margin-bottom:16px; display:flex; align-items:center; gap:12px;">
        <span style="font-size:1.6rem; font-weight:800; color:var(--accent-secondary);">⭐ ${res.avg_rating}/5.0</span>
        <span style="color:var(--text-muted); font-size:0.9rem;">(${res.total_reviews} đánh giá từ khách đã mua)</span>
      </div>
      <div style="display:flex; flex-direction:column; gap:14px;">
        ${items.map(r => `
          <div style="padding:16px; background:var(--bg-main); border:1px solid var(--border-subtle); border-radius:var(--radius-md);">
            <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
              <strong style="color:var(--text-main);">${escapeHtml(r.customer_name || 'Khách hàng')}</strong>
              <span style="color:var(--accent-secondary);">${"⭐".repeat(r.rating)}</span>
            </div>
            <p style="color:var(--text-muted); font-size:0.92rem; margin-bottom:8px;">${escapeHtml(r.comment || '')}</p>
            ${r.image_url ? `<img src="${escapeHtml(r.image_url)}" alt="Ảnh đánh giá" style="max-width:140px; border-radius:8px; margin-bottom:8px; display:block;">` : ''}
            <div style="font-size:0.78rem; color:var(--text-dim);">${formatDateTime(r.created_at)}</div>
            ${r.store_reply ? `
              <div style="margin-top:10px; padding:10px 14px; background:rgba(249,115,22,0.1); border-left:3px solid var(--accent-primary); border-radius:6px; font-size:0.88rem;">
                <strong style="color:var(--accent-primary);">🌙 Phản hồi từ NightFood:</strong>
                <div style="color:var(--text-main); margin-top:4px;">${escapeHtml(r.store_reply)}</div>
              </div>
            ` : ''}
          </div>
        `).join("")}
      </div>
    `;
  } catch (err) {
    listEl.innerHTML = `<div style="color:var(--text-dim);">Không thể tải đánh giá.</div>`;
  }
}
