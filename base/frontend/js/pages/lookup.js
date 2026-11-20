// Logic Theo dõi đơn hàng & Đơn của tôi theo tab trạng thái (T3D29F3, T3D28EF, T3D2909, T3D2D99, T3D2587)

let currentTrackedCode = "";
let currentTrackedPhone = "";
let autoRefreshTimer = null;
let currentMyOrderTabStatus = "";

document.addEventListener("DOMContentLoaded", async () => {
  const urlParams = new URLSearchParams(window.location.search);
  const codeParam = urlParams.get("code");
  const phoneParam = urlParams.get("phone");

  if (codeParam) {
    document.getElementById("lookup-code").value = codeParam.trim();
  }
  if (phoneParam) {
    document.getElementById("lookup-phone").value = phoneParam.trim();
    localStorage.setItem("nightfood_last_phone", phoneParam.trim());
  } else {
    const savedPhone = localStorage.getItem("nightfood_last_phone");
    if (savedPhone) {
      document.getElementById("lookup-phone").value = savedPhone;
    }
  }

  if (codeParam && (phoneParam || document.getElementById("lookup-phone").value)) {
    await performLookup(codeParam.trim(), document.getElementById("lookup-phone").value.trim());
  }

  const form = document.getElementById("lookup-form");
  if (form) {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const code = document.getElementById("lookup-code").value.trim().toUpperCase();
      const phone = document.getElementById("lookup-phone").value.trim();

      if (!code || !phone) {
        showToast("Vui lòng nhập cả Mã đơn và Số điện thoại", "warning");
        return;
      }
      localStorage.setItem("nightfood_last_phone", phone);
      await performLookup(code, phone);
      await loadMyOrdersList();
    });
  }

  // Gắn sự kiện Tab trạng thái Đơn của tôi
  const tabsWrap = document.getElementById("my-orders-status-tabs");
  if (tabsWrap) {
    tabsWrap.querySelectorAll(".category-tab").forEach(tab => {
      tab.addEventListener("click", async () => {
        tabsWrap.querySelectorAll(".category-tab").forEach(t => t.classList.remove("active"));
        tab.classList.add("active");
        currentMyOrderTabStatus = tab.getAttribute("data-status") || "";
        await loadMyOrdersList();
      });
    });
  }

  const refreshMyBtn = document.getElementById("btn-refresh-my-orders");
  if (refreshMyBtn) {
    refreshMyBtn.addEventListener("click", () => loadMyOrdersList());
  }

  await loadMyOrdersList();
});

async function loadMyOrdersList() {
  const listEl = document.getElementById("my-orders-list-container");
  if (!listEl) return;

  const guestToken = typeof CartStorage !== "undefined" ? CartStorage.getGuestToken() : "";
  const phone = (document.getElementById("lookup-phone")?.value || localStorage.getItem("nightfood_last_phone") || "").trim();

  try {
    const params = {};
    if (currentMyOrderTabStatus) params.status = currentMyOrderTabStatus;
    if (guestToken) params.guest_token = guestToken;
    if (phone) params.phone = phone;

    const orders = await api.get("/orders/my", params);
    if (!orders || orders.length === 0) {
      listEl.innerHTML = `
        <div style="text-align:center; padding:28px; color:var(--text-dim);">
          Chưa có đơn hàng nào ở trạng thái này. (Nhập SĐT của bạn ở trên để đồng bộ các đơn đã đặt)
        </div>
      `;
      return;
    }

    listEl.innerHTML = orders.map(ord => `
      <div style="padding:14px 16px; background:var(--bg-main); border:1px solid var(--border-subtle); border-radius:var(--radius-md); margin-bottom:12px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
        <div>
          <div style="display:flex; align-items:center; gap:10px; margin-bottom:4px;">
            <strong style="font-size:1.1rem; color:var(--accent-secondary);">${escapeHtml(ord.order_code)}</strong>
            <span class="badge-status badge-${ord.status}">${escapeHtml(ord.status_display)}</span>
          </div>
          <div style="font-size:0.84rem; color:var(--text-muted);">
            ${(ord.items || []).map(i => `${escapeHtml(i.dish_name)} x${i.quantity}`).join(", ")}
          </div>
          <div style="font-size:0.78rem; color:var(--text-dim); margin-top:2px;">Đặt lúc: ${formatDateTime(ord.created_at)}</div>
        </div>
        <div style="text-align:right; display:flex; flex-direction:column; align-items:flex-end; gap:8px;">
          <div style="font-size:1.1rem; font-weight:800; color:var(--accent-secondary);">${formatVND(ord.total_amount)}</div>
          <div style="display:flex; gap:8px;">
            <button type="button" class="btn btn-secondary" style="padding:5px 12px; font-size:0.8rem;" onclick="trackOrderFromList('${escapeHtml(ord.order_code)}')">
              👁️ Theo dõi đơn
            </button>
            <button type="button" class="btn btn-primary" style="padding:5px 12px; font-size:0.8rem;" onclick='quickReorderItems(${JSON.stringify(ord.items || [])})'>
              🔁 Đặt lại
            </button>
          </div>
        </div>
      </div>
    `).join("");
  } catch (err) {
    listEl.innerHTML = `<div style="text-align:center; padding:20px; color:var(--text-dim);">Nhập số điện thoại nhận hàng ở trên để xem danh sách đơn của bạn.</div>`;
  }
}

async function trackOrderFromList(orderCode) {
  document.getElementById("lookup-code").value = orderCode;
  const phone = document.getElementById("lookup-phone").value.trim() || localStorage.getItem("nightfood_last_phone") || "";
  await performLookup(orderCode, phone);
  window.scrollTo({ top: 100, behavior: "smooth" });
}

function quickReorderItems(items) {
  if (!items || !items.length || typeof CartStorage === "undefined") return;
  items.forEach(it => {
    CartStorage.addItem(it.dish_id, it.quantity || 1, null, it.note || "", null, it.option_name || null);
  });
  showToast("Đã thêm toàn bộ món từ đơn cũ vào giỏ hàng!", "success");
  setTimeout(() => {
    window.location.href = "cart.html";
  }, 600);
}

async function performLookup(orderCode, phone, isSilentRefresh = false) {
  const container = document.getElementById("lookup-result-container");
  const submitBtn = document.getElementById("btn-lookup-submit");
  const guestToken = typeof CartStorage !== "undefined" ? CartStorage.getGuestToken() : "";

  if (!isSilentRefresh) {
    container.innerHTML = `
      <div class="card-panel" style="text-align:center; padding:40px; color:var(--text-dim);">
        ⏳ Đang tra cứu thông tin đơn hàng...
      </div>
    `;
  }

  try {
    if (!isSilentRefresh && submitBtn) {
      submitBtn.disabled = true;
      submitBtn.textContent = "Đang tra cứu...";
    }

    let data = null;
    if (phone && phone.length === 10) {
      data = await api.post("/orders/lookup", {
        order_code: orderCode,
        phone: phone,
      });
    } else {
      data = await api.get(`/orders/${encodeURIComponent(orderCode)}/track`, {
        guest_token: guestToken,
        phone: phone || undefined,
      });
    }

    currentTrackedCode = data.order_code;
    currentTrackedPhone = phone;

    renderLookupResult(data);
    setupAutoRefresh15s(data);

  } catch (err) {
    if (isSilentRefresh) return;
    let errMsg = err.message || "Không tìm thấy đơn hàng phù hợp";
    if (err.status === 429) {
      errMsg = `⚠️ Bạn đã thử sai quá số lần cho phép. ${err.message}`;
    }

    container.innerHTML = `
      <div class="card-panel" style="text-align:center; padding:36px 20px; border-color:rgba(239,68,68,0.4);">
        <div style="font-size:2.8rem; margin-bottom:10px;">❌</div>
        <h3 style="color:var(--danger); margin-bottom:8px;">Không Thể Tra Cứu</h3>
        <p style="color:var(--text-muted); font-size:0.95rem;">${escapeHtml(errMsg)}</p>
      </div>
    `;
  } finally {
    if (!isSilentRefresh && submitBtn) {
      submitBtn.disabled = false;
      submitBtn.textContent = "🔍 Tra Cứu Ngay";
    }
  }
}

function setupAutoRefresh15s(data) {
  if (autoRefreshTimer) {
    clearInterval(autoRefreshTimer);
    autoRefreshTimer = null;
  }
  // Tự động cập nhật thanh tiến trình trạng thái mỗi 15 giây khi đơn đang xử lý (T3D29F3)
  if (data && !["completed", "cancelled"].includes(data.status)) {
    autoRefreshTimer = setInterval(() => {
      if (currentTrackedCode) {
        performLookup(currentTrackedCode, currentTrackedPhone, true);
      }
    }, 15000);
  }
}

async function handleCustomerCancelOrder(orderCode) {
  const reason = prompt("Nhập lý do bạn muốn huỷ đơn hàng này:", "Đặt nhầm món / Muốn đổi món");
  if (reason === null) return;
  const guestToken = typeof CartStorage !== "undefined" ? CartStorage.getGuestToken() : "";
  try {
    await api.post(`/orders/${encodeURIComponent(orderCode)}/cancel`, {
      phone: currentTrackedPhone || null,
      guest_token: guestToken || null,
      reason: reason.trim() || "Khách yêu cầu huỷ đơn",
    });
    showToast("Đã huỷ đơn hàng thành công!", "info");
    await performLookup(orderCode, currentTrackedPhone);
    await loadMyOrdersList();
  } catch (err) {
    showToast(err.message, "error");
  }
}

function renderLookupResult(data) {
  const container = document.getElementById("lookup-result-container");

  const statusSteps = [
    { key: "pending", label: "Chờ xác nhận" },
    { key: "confirmed", label: "Đã xác nhận" },
    { key: "preparing", label: "Đang chuẩn bị" },
    { key: "delivering", label: "Đang giao" },
    { key: "completed", label: "Hoàn thành" },
  ];

  const isCancelled = data.status === "cancelled";
  const currentIndex = statusSteps.findIndex(s => s.key === data.status);

  const timelineHtml = isCancelled
    ? `
      <div style="background-color:rgba(239,68,68,0.15); border:1px solid rgba(239,68,68,0.3); padding:16px; border-radius:var(--radius-md); text-align:center; margin-bottom:24px;">
        <span style="font-size:1.4rem;">🚫</span>
        <div style="color:#f87171; font-weight:700; font-size:1.1rem; margin-top:4px;">Đơn hàng đã bị hủy</div>
        <div style="color:var(--text-muted); font-size:0.85rem;">Vui lòng liên hệ quán nếu bạn cần hỗ trợ thêm.</div>
      </div>
    `
    : `
      <div style="display:flex; justify-content:space-between; margin-bottom:28px; position:relative; overflow-x:auto; padding: 10px 4px;">
        ${statusSteps.map((step, idx) => {
          const isPassed = idx <= currentIndex;
          const isCurrent = idx === currentIndex;
          const textColor = isPassed ? "var(--text-main)" : "var(--text-dim)";
          return `
            <div style="display:flex; flex-direction:column; align-items:center; text-align:center; min-width:80px; z-index:1;">
              <div style="width:36px; height:36px; border-radius:50%; background-color:${isCurrent ? 'var(--accent-primary)' : (isPassed ? '#10b981' : 'var(--bg-elevated)')}; display:flex; align-items:center; justify-content:center; color:#fff; font-weight:700; font-size:0.85rem; margin-bottom:8px; box-shadow:${isCurrent ? '0 0 12px rgba(249,115,22,0.6)' : 'none'};">
                ${isPassed ? (isCurrent ? '●' : '✓') : (idx + 1)}
              </div>
              <span style="font-size:0.78rem; font-weight:${isCurrent ? '700' : '500'}; color:${textColor};">${step.label}</span>
            </div>
          `;
        }).join("")}
      </div>
    `;

  const itemsHtml = data.items.map(it => `
    <div style="display:flex; justify-content:space-between; align-items:center; padding:10px 0; border-bottom:1px solid rgba(255,255,255,0.06); font-size:0.92rem;">
      <div>
        <span style="font-weight:600; color:var(--text-main);">${escapeHtml(it.dish_name)}</span>
        ${it.option_name ? `<span style="color:var(--accent-primary); font-size:0.82rem;"> (+${escapeHtml(it.option_name)})</span>` : ''}
        ${it.note ? `<div style="color:var(--text-dim); font-size:0.78rem;">📝 Ghi chú: ${escapeHtml(it.note)}</div>` : ''}
        <div style="color:var(--text-dim); font-size:0.82rem;">${formatVND(it.unit_price)} × ${it.quantity}</div>
      </div>
      <div style="font-weight:700; color:var(--accent-secondary);">${formatVND(it.subtotal)}</div>
    </div>
  `).join("");

  const historyListHtml = (data.status_histories && data.status_histories.length > 0)
    ? `
      <div style="margin-top:16px; padding:12px; background:var(--bg-main); border-radius:var(--radius-sm); font-size:0.82rem;">
        <div style="font-weight:700; color:var(--text-muted); margin-bottom:6px;">🕒 Dòng thời gian trạng thái:</div>
        ${data.status_histories.map(h => `
          <div style="display:flex; justify-content:space-between; padding:3px 0; color:var(--text-dim);">
            <span>• <strong>${escapeHtml(h.new_status)}</strong>: ${escapeHtml(h.note || '')}</span>
            <span>${formatDateTime(h.changed_at)}</span>
          </div>
        `).join("")}
      </div>
    `
    : "";

  container.innerHTML = `
    <div class="card-panel">
      <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:16px; border-bottom:1px solid var(--border-color); padding-bottom:12px; flex-wrap:wrap; gap:10px;">
        <div>
          <div style="color:var(--text-dim); font-size:0.82rem; text-transform:uppercase;">
            Mã đơn hàng · <span style="color:#4ade80;">🔄 Tự cập nhật mỗi 15 giây</span>
          </div>
          <div style="font-size:1.6rem; font-weight:800; color:var(--accent-secondary);">${escapeHtml(data.order_code)}</div>
        </div>
        <div style="text-align:right;">
          <span class="badge-status badge-${data.status}">${escapeHtml(data.status_display)}</span>
          <div style="color:var(--text-dim); font-size:0.82rem; margin-top:4px;">${formatDateTime(data.created_at)}</div>
        </div>
      </div>

      <!-- Trực quan hóa tiến trình trạng thái -->
      ${timelineHtml}

      <!-- Nút Huỷ đơn khi còn ở trạng thái Chờ xác nhận (T3D29F3, T3D2909) & Nút Đặt lại -->
      <div style="display:flex; justify-content:flex-end; gap:10px; margin-bottom:16px; flex-wrap:wrap;">
        ${data.status === "pending" ? `
          <button type="button" class="btn btn-danger" style="padding:7px 14px; font-size:0.85rem;" onclick="handleCustomerCancelOrder('${escapeHtml(data.order_code)}')">
            ❌ Huỷ Đơn Hàng
          </button>
        ` : ''}
        <button type="button" class="btn btn-secondary" style="padding:7px 14px; font-size:0.85rem;" onclick='quickReorderItems(${JSON.stringify(data.items || [])})'>
          🔁 Đặt Lại Đơn Này
        </button>
      </div>

      <!-- Thông tin nhận hàng -->
      <div style="background-color:var(--bg-main); border-radius:var(--radius-md); padding:16px; margin-bottom:20px; font-size:0.92rem;">
        <div style="margin-bottom:6px;"><span style="color:var(--text-dim);">Khách hàng:</span> <strong style="color:var(--text-main);">${escapeHtml(data.customer_name)}</strong></div>
        <div style="margin-bottom:6px;"><span style="color:var(--text-dim);">Địa chỉ nhận:</span> <span style="color:var(--text-muted);">${escapeHtml(data.masked_address)}</span> (${escapeHtml(data.area || 'Nội thành')})</div>
        <div style="margin-bottom:6px;"><span style="color:var(--text-dim);">Giờ giao mong muốn:</span> <span style="color:var(--text-main);">${escapeHtml(data.desired_delivery_time || 'Giao ngay')}</span></div>
        <div><span style="color:var(--text-dim);">Hình thức:</span> <span style="color:#4ade80; font-weight:600;">${escapeHtml(data.payment_method)}</span></div>
      </div>

      <!-- Danh sách món -->
      <h4 style="font-size:1rem; font-weight:700; margin-bottom:10px; color:var(--text-main);">Chi Tiết Món Ăn</h4>
      <div style="margin-bottom:16px;">
        ${itemsHtml}
      </div>

      <div style="display:flex; justify-content:space-between; padding-top:12px; border-top:1px solid var(--border-color); font-size:1.3rem; font-weight:800; color:var(--accent-secondary);">
        <span>Tổng thanh toán:</span>
        <span>${formatVND(data.total_amount)}</span>
      </div>

      ${historyListHtml}

      ${data.status === "completed" ? `
        <div style="margin-top:24px; padding-top:18px; border-top:1px solid var(--border-color);">
          <h4 style="font-size:1.05rem; font-weight:700; margin-bottom:12px; color:var(--accent-secondary);">⭐ Đánh Giá Món Ăn Trong Đơn Đã Hoàn Thành (T3D2D99)</h4>
          ${data.items.map(it => `
            <div style="background:var(--bg-main); padding:14px; border-radius:var(--radius-sm); margin-bottom:12px; border:1px solid var(--border-subtle);">
              <div style="font-weight:700; margin-bottom:8px;">🍜 ${escapeHtml(it.dish_name)}</div>
              <div style="display:grid; grid-template-columns: 120px 1fr auto; gap:10px; align-items:center; flex-wrap:wrap;">
                <select id="rev-star-${it.dish_id}" class="form-control" style="padding:6px 10px; font-size:0.85rem;">
                  <option value="5">⭐⭐⭐⭐⭐ (5)</option>
                  <option value="4">⭐⭐⭐⭐ (4)</option>
                  <option value="3">⭐⭐⭐ (3)</option>
                  <option value="2">⭐⭐ (2)</option>
                  <option value="1">⭐ (1)</option>
                </select>
                <input type="text" id="rev-comment-${it.dish_id}" class="form-control" placeholder="Nhận xét hương vị món ăn..." style="padding:6px 10px; font-size:0.85rem;">
                <button type="button" class="btn btn-primary" style="padding:6px 14px; font-size:0.85rem;" onclick="submitOrderDishReview('${escapeHtml(data.order_code)}', ${it.dish_id})">
                  Gửi Đánh Giá
                </button>
              </div>
            </div>
          `).join("")}
        </div>
      ` : ''}
    </div>
  `;
}

async function submitOrderDishReview(orderCode, dishId) {
  const ratingEl = document.getElementById(`rev-star-${dishId}`);
  const commentEl = document.getElementById(`rev-comment-${dishId}`);
  const phoneEl = document.getElementById("lookup-phone");
  const rating = ratingEl ? parseInt(ratingEl.value) : 5;
  const comment = commentEl ? commentEl.value.trim() : "";
  const phone = phoneEl ? phoneEl.value.trim() : "";
  const guestToken = typeof CartStorage !== "undefined" ? CartStorage.getGuestToken() : "";
  try {
    await api.post("/reviews", {
      order_code: orderCode,
      phone: phone || null,
      guest_token: guestToken || null,
      dish_id: dishId,
      rating,
      comment: comment || "Món ăn rất ngon, giao nhanh!",
    });
    showToast("Cảm ơn bạn đã gửi đánh giá món ăn! ⭐", "success");
  } catch (err) {
    showToast(err.message, "error");
  }
}
