// Logic Quản lý Giỏ hàng: Hiển thị tuỳ chọn, sửa ghi chú, tính tiền qua server & Mobile Drawer (T3D2887, T3D262C)

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

  let calcData = null;
  try {
    calcData = await api.post("/cart/calculate", {
      items: cartItems.map(it => ({
        dish_id: it.dish_id,
        quantity: it.quantity,
        dish_option_id: it.dish_option_id || null,
        selected_option_ids: it.selected_option_ids || null,
        note: it.note || null,
      })),
      area: "Nội thành",
    });
  } catch (err) {
    console.warn("Không thể gọi API tính tiền giỏ hàng:", err);
  }

  const defaultImg = "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=500&auto=format&fit=crop&q=60";
  const serverItems = (calcData && calcData.items) ? calcData.items : [];
  const totalAmount = calcData ? calcData.subtotal : 0;
  const hasUnavailableItem = calcData ? calcData.has_unavailable_item : false;
  const warnings = (calcData && calcData.warnings) ? calcData.warnings : [];

  const tableRows = cartItems.map((it, idx) => {
    const sItem = serverItems[idx];
    if (!sItem || !sItem.is_active) {
      return `
        <tr>
          <td colspan="4" style="color:var(--danger);">
            ⚠️ Món ăn (ID=${it.dish_id}) không còn kinh doanh hoặc đã bị ẩn. Vui lòng xóa khỏi giỏ.
          </td>
          <td>
            <button class="btn btn-danger" style="padding:4px 8px; font-size:0.8rem;" onclick="CartStorage.removeItemByIndex(${idx})">Xóa</button>
          </td>
        </tr>
      `;
    }

    const optDisplay = sItem.option_name || it.option_name || "";

    return `
      <tr>
        <td>
          <div style="display:flex; align-items:flex-start; gap:14px;">
            <img src="${sItem.image_url || defaultImg}" alt="${escapeHtml(sItem.dish_name)}" style="width:64px; height:64px; object-fit:cover; border-radius:var(--radius-sm);" onerror="this.src='${defaultImg}'">
            <div style="flex:1;">
              <div style="font-weight:700; color:var(--text-main); font-size:1rem;">${escapeHtml(sItem.dish_name)}</div>
              ${optDisplay ? `<div style="color:var(--accent-primary); font-size:0.82rem; font-weight:600; margin-top:2px;">+ Tuỳ chọn: ${escapeHtml(optDisplay)}</div>` : ''}
              ${!sItem.is_available ? '<div style="color:#ef4444; font-size:0.8rem; font-weight:700; margin-top:2px;">[HẾT HÀNG - CẦN XÓA HOẶC ĐỔI MÓN]</div>' : ''}
              <div style="margin-top:8px; display:flex; align-items:center; gap:6px;">
                <input 
                  type="text" 
                  class="form-control" 
                  placeholder="Ghi chú món (VD: Ít cay, không hành...)" 
                  value="${escapeHtml(it.note || '')}" 
                  style="padding:5px 10px; font-size:0.8rem; max-width:240px;"
                  onchange="CartStorage.updateNoteByIndex(${idx}, this.value)">
              </div>
            </div>
          </div>
        </td>
        <td style="color:var(--accent-secondary); font-weight:700;">
          ${formatVND(sItem.unit_price)}
          ${sItem.option_extra_price > 0 ? `<div style="font-size:0.75rem; color:var(--text-dim);">(Gốc ${formatVND(sItem.base_price)} + ${formatVND(sItem.option_extra_price)})</div>` : ''}
        </td>
        <td>
          <div class="qty-control">
            <button class="qty-btn" onclick="adjustCartLineQty(${idx}, ${it.quantity - 1})">-</button>
            <div class="qty-val">${it.quantity}</div>
            <button class="qty-btn" onclick="adjustCartLineQty(${idx}, ${it.quantity + 1})">+</button>
          </div>
        </td>
        <td style="color:var(--accent-secondary); font-weight:800;">${formatVND(sItem.line_total)}</td>
        <td>
          <button class="btn btn-danger" style="padding:6px 10px; font-size:0.8rem;" onclick="CartStorage.removeItemByIndex(${idx})">🗑️ Xóa</button>
        </td>
      </tr>
    `;
  }).join("");

  container.innerHTML = `
    <div style="display:grid; grid-template-columns: 2fr 1fr; gap:24px;">
      <!-- Danh sách món kèm tuỳ chọn và ghi chú -->
      <div class="card-panel" style="padding:20px;">
        <div class="table-responsive">
          <table class="data-table">
            <thead>
              <tr>
                <th>Món ăn & Tuỳ chọn / Ghi chú</th>
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
            <span>Tạm tính (${CartStorage.getTotalCount()} món):</span>
            <span style="font-weight:600; color:var(--text-main);">${formatVND(totalAmount)}</span>
          </div>
          <div style="display:flex; justify-content:space-between; margin-bottom:14px; color:var(--text-muted);">
            <span>Phí giao hàng đêm:</span>
            <span style="color:#4ade80; font-weight:600;">Tính theo khu vực ở bước sau</span>
          </div>
          <div style="display:flex; justify-content:space-between; padding-top:14px; border-top:1px solid var(--border-color); font-size:1.25rem; font-weight:800; color:var(--accent-secondary); margin-bottom:20px;">
            <span>Tạm tính:</span>
            <span>${formatVND(totalAmount)}</span>
          </div>

          ${warnings.length > 0 ? `
            <div style="background-color:rgba(239,68,68,0.15); border:1px solid rgba(239,68,68,0.3); color:#f87171; padding:12px; border-radius:var(--radius-sm); font-size:0.85rem; margin-bottom:16px;">
              ${warnings.map(w => `<div>⚠️ ${escapeHtml(w)}</div>`).join("")}
            </div>
          ` : ''}

          <a 
            href="${hasUnavailableItem ? '#' : 'checkout.html'}" 
            class="btn btn-primary" 
            style="width:100%; padding:14px; font-size:1.05rem;"
            ${hasUnavailableItem ? 'disabled style="opacity:0.5; pointer-events:none;"' : ''}>
            👉 Tiến Hành Thanh Toán
          </a>

          <div style="text-align:center; margin-top:12px;">
            <a href="dishes.html" style="font-size:0.88rem; color:var(--accent-primary);">+ Tiếp tục chọn thêm món</a>
          </div>
        </div>
      </div>
    </div>
  `;
}

function adjustCartLineQty(index, newQty) {
  if (newQty <= 0) {
    CartStorage.removeItemByIndex(index);
  } else if (newQty > 99) {
    showToast("Số lượng mỗi món tối đa là 99", "warning");
  } else {
    CartStorage.updateQuantityByIndex(index, newQty);
  }
}
