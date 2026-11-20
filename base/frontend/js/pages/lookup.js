// Logic Tra cứu đơn hàng (FR-07, BR-12, TC-23, TC-24, TC-33)

document.addEventListener("DOMContentLoaded", () => {
  const urlParams = new URLSearchParams(window.location.search);
  const codeParam = urlParams.get("code");
  const phoneParam = urlParams.get("phone");

  if (codeParam) {
    document.getElementById("lookup-code").value = codeParam.trim();
  }
  if (phoneParam) {
    document.getElementById("lookup-phone").value = phoneParam.trim();
  }

  if (codeParam && phoneParam) {
    performLookup(codeParam.trim(), phoneParam.trim());
  }

  const form = document.getElementById("lookup-form");
  if (form) {
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      const code = document.getElementById("lookup-code").value.trim().toUpperCase();
      const phone = document.getElementById("lookup-phone").value.trim();

      if (!code || !phone) {
        showToast("Vui lòng nhập cả Mã đơn và Số điện thoại", "warning");
        return;
      }
      performLookup(code, phone);
    });
  }
});

async function performLookup(orderCode, phone) {
  const container = document.getElementById("lookup-result-container");
  const submitBtn = document.getElementById("btn-lookup-submit");

  container.innerHTML = `
    <div class="card-panel" style="text-align:center; padding:40px; color:var(--text-dim);">
      ⏳ Đang tra cứu thông tin đơn hàng...
    </div>
  `;

  try {
    submitBtn.disabled = true;
    submitBtn.textContent = "Đang tra cứu...";

    const data = await api.post("/orders/lookup", {
      order_code: orderCode,
      phone: phone,
    });

    renderLookupResult(data);

  } catch (err) {
    let errMsg = err.message || "Không tìm thấy đơn hàng phù hợp";

    // Xử lý rate limit (HTTP 429, TC-33)
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
    submitBtn.disabled = false;
    submitBtn.textContent = "🔍 Tra Cứu Ngay";
  }
}

function renderLookupResult(data) {
  const container = document.getElementById("lookup-result-container");

  const statusSteps = [
    { key: "pending", label: "Chờ xác nhận" },
    { key: "confirmed", label: "Đã xác nhận" },
    { key: "preparing", label: "Đang nấu món" },
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
          const color = isPassed ? "var(--accent-primary)" : "var(--border-color)";
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
        ${it.option_name ? `<span style="color:var(--text-dim); font-size:0.82rem;"> (+${escapeHtml(it.option_name)})</span>` : ''}
        <div style="color:var(--text-dim); font-size:0.82rem;">${formatVND(it.unit_price)} × ${it.quantity}</div>
      </div>
      <div style="font-weight:700; color:var(--accent-secondary);">${formatVND(it.subtotal)}</div>
    </div>
  `).join("");

  container.innerHTML = `
    <div class="card-panel">
      <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:16px; border-bottom:1px solid var(--border-color); padding-bottom:12px; flex-wrap:wrap; gap:10px;">
        <div>
          <div style="color:var(--text-dim); font-size:0.82rem; text-transform:uppercase;">Mã đơn hàng</div>
          <div style="font-size:1.6rem; font-weight:800; color:var(--accent-secondary);">${escapeHtml(data.order_code)}</div>
        </div>
        <div style="text-align:right;">
          <span class="badge-status badge-${data.status}">${escapeHtml(data.status_display)}</span>
          <div style="color:var(--text-dim); font-size:0.82rem; margin-top:4px;">${formatDateTime(data.created_at)}</div>
        </div>
      </div>

      <!-- Trực quan hóa tiến trình trạng thái -->
      ${timelineHtml}

      <!-- Thông tin nhận hàng (ẩn bớt địa chỉ để bảo mật per 3.7) -->
      <div style="background-color:var(--bg-main); border-radius:var(--radius-md); padding:16px; margin-bottom:20px; font-size:0.92rem;">
        <div style="margin-bottom:6px;"><span style="color:var(--text-dim);">Khách hàng:</span> <strong style="color:var(--text-main);">${escapeHtml(data.customer_name)}</strong></div>
        <div style="margin-bottom:6px;"><span style="color:var(--text-dim);">Địa chỉ nhận:</span> <span style="color:var(--text-muted);">${escapeHtml(data.masked_address)}</span></div>
        <div><span style="color:var(--text-dim);">Hình thức:</span> <span style="color:#4ade80; font-weight:600;">Thanh toán khi nhận hàng (${data.payment_method})</span></div>
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
    </div>
  `;
}
