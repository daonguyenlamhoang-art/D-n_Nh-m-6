// Logic Quản lý Giỏ hàng (FR-04, FR-05, TC-05..08, TC-27, TC-38)

let verifiedDishes = {};

document.addEventListener("DOMContentLoaded", async () => {
  await renderCart();

  window.addEventListener("nightfood_cart_changed", async () => {
    await renderCart();
  });
});

async function renderCart() {
  const container = document.getElementById("cart-content");
  if (!container) return;

  const cartItems = CartStorage.getItems();

  if (!cartItems || cartItems.length === 0) {
    container.innerHTML = `
      <div class="card-panel" style="text-align:center; padding: 60px 20px;">
        <div style="font-size:3.5rem; margin-bottom:14px;">🛍️</div>
        <h2 style="color:var(--text-main); margin-bottom:8px;">Giỏ hàng của bạn đang trống</h2>
        <p style="color:var(--text-muted); font-size:0.95rem; margin-bottom:24px;">Bạn chưa chọn món ăn đêm nào. Hãy chọn vài món ngon để nạp năng lượng nhé!</p>
        <a href="dishes.html" class="btn btn-primary" style="padding:12px 28px;">🍜 Khám phá Thực đơn</a>
      </div>
    `;
    return;
  }

  // Đối chiếu lại với dữ liệu hiện tại từ API theo yêu cầu FR-05
  try {
    const ids = cartItems.map(it => it.dish_id).join(",");
    const freshDishes = await api.get("/dishes", { ids });
    verifiedDishes = {};
    freshDishes.forEach(d => {
      verifiedDishes[d.id] = d;
    });
  } catch (err) {
    console.warn("Không thể tải thông tin món mới nhất:", err);
  }

  let totalAmount = 0;
  let hasUnavailableItem = false;

  const tableRows = cartItems.map(it => {
    const dish = verifiedDishes[it.dish_id];
    const defaultImg = "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=500&auto=format&fit=crop&q=60";

    if (!dish) {
      hasUnavailableItem = true;
      return `
        <tr>
          <td colspan="4" style="color:var(--danger);">
            ⚠️ Món ăn (ID=${it.dish_id}) không còn kinh doanh hoặc đã bị ẩn. Vui lòng xóa khỏi giỏ.
          </td>
          <td>
            <button class="btn btn-danger" style="padding:4px 8px; font-size:0.8rem;" onclick="CartStorage.removeItem(${it.dish_id})">Xóa</button>
          </td>
        </tr>
      `;
    }

    const isAvailable = dish.is_available;
    if (!isAvailable) {
      hasUnavailableItem = true;
    }

    const unitPrice = dish.price;
    const itemSubtotal = unitPrice * it.quantity;
    totalAmount += itemSubtotal;

    return `
      <tr>
        <td style="display:flex; align-items:center; gap:14px;">
          <img src="${dish.image_url || defaultImg}" alt="${escapeHtml(dish.name)}" style="width:60px; height:60px; object-fit:cover; border-radius:var(--radius-sm);" onerror="this.src='${defaultImg}'">
          <div>
            <div style="font-weight:700; color:var(--text-main); font-size:1rem;">${escapeHtml(dish.name)}</div>
            ${!isAvailable ? '<span style="color:#ef4444; font-size:0.8rem; font-weight:700;">[HẾT HÀNG - CẦN XÓA HOẶC ĐỔI MÓN]</span>' : ''}
          </div>
        </td>
        <td style="color:var(--accent-secondary); font-weight:700;">${formatVND(unitPrice)}</td>
        <td>
          <div class="qty-control">
            <button class="qty-btn" onclick="adjustItemQty(${it.dish_id}, ${it.quantity - 1})">-</button>
            <div class="qty-val">${it.quantity}</div>
            <button class="qty-btn" onclick="adjustItemQty(${it.dish_id}, ${it.quantity + 1})">+</button>
          </div>
        </td>
        <td style="color:var(--accent-secondary); font-weight:800;">${formatVND(itemSubtotal)}</td>
        <td>
          <button class="btn btn-danger" style="padding:6px 10px; font-size:0.8rem;" onclick="CartStorage.removeItem(${it.dish_id})">🗑️ Xóa</button>
        </td>
      </tr>
    `;
  }).join("");

  container.innerHTML = `
    <div style="display:grid; grid-template-columns: 2fr 1fr; gap:24px;">
      <!-- Danh sách món -->
      <div class="card-panel" style="padding:20px;">
        <div class="table-responsive">
          <table class="data-table">
            <thead>
              <tr>
                <th>Món ăn</th>
                <th>Đơn giá</th>
                <th>Số lượng</th>
                <th>Thành tiền</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              ${tableRows}
            </tbody>
          </table>
        </div>
      </div>

      <!-- Tổng hóa đơn & Đặt hàng -->
      <div>
        <div class="card-panel">
          <h3 style="font-size:1.15rem; font-weight:700; margin-bottom:16px; border-bottom:1px solid var(--border-color); padding-bottom:10px;">
            Hóa Đơn Tạm Tính
          </h3>
          <div style="display:flex; justify-content:space-between; margin-bottom:10px; color:var(--text-muted);">
            <span>Tạm tính món:</span>
            <span style="font-weight:600; color:var(--text-main);">${formatVND(totalAmount)}</span>
          </div>
          <div style="display:flex; justify-content:space-between; margin-bottom:14px; color:var(--text-muted);">
            <span>Phí giao hàng đêm:</span>
            <span style="color:#4ade80; font-weight:600;">Miễn phí (COD)</span>
          </div>
          <div style="display:flex; justify-content:space-between; padding-top:14px; border-top:1px solid var(--border-color); font-size:1.25rem; font-weight:800; color:var(--accent-secondary); margin-bottom:20px;">
            <span>Tổng cộng:</span>
            <span>${formatVND(totalAmount)}</span>
          </div>

          ${hasUnavailableItem ? `
            <div style="background-color:rgba(239,68,68,0.15); border:1px solid rgba(239,68,68,0.3); color:#f87171; padding:12px; border-radius:var(--radius-sm); font-size:0.85rem; margin-bottom:16px;">
              ⚠️ Trong giỏ có món đã hết hàng hoặc ngừng bán. Vui lòng xóa món đó trước khi tiếp tục.
            </div>
          ` : ''}

          <a 
            href="${hasUnavailableItem ? '#' : 'checkout.html'}" 
            class="btn btn-primary" 
            style="width:100%; padding:14px; font-size:1.05rem;"
            ${hasUnavailableItem ? 'disabled style="opacity:0.5; pointer-events:none;"' : ''}>
            👉 Tiến Hành Đặt Hàng
          </a>

          <div style="text-align:center; margin-top:12px;">
            <a href="dishes.html" style="font-size:0.88rem; color:var(--accent-primary);">+ Tiếp tục chọn thêm món</a>
          </div>
        </div>
      </div>
    </div>
  `;
}

function adjustItemQty(dishId, newQty) {
  if (newQty <= 0) {
    CartStorage.removeItem(dishId);
  } else if (newQty > 99) {
    showToast("Số lượng mỗi món tối đa là 99", "warning");
  } else {
    CartStorage.updateQuantity(dishId, newQty);
  }
}
