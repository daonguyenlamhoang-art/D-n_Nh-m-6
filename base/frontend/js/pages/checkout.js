// Logic Trang Thanh Toán Checkout: Sổ địa chỉ, Giờ giao, Mã giảm giá, Khu vực phí ship, COD/QR (T3D28A1, T3D286D, T3D28BB)

let checkoutItems = [];
let currentSubtotal = 0;
let currentShippingFee = 0;
let currentDiscount = 0;
let currentExpectedTotal = 0;
let appliedVoucherCode = null;
let isSubmitting = false;

const ADDRESS_BOOK_KEY = "nightfood_address_book";

document.addEventListener("DOMContentLoaded", async () => {
  initAddressBook();
  restoreSavedPaymentMethod();
  await recalculateCheckoutSummary();

  const form = document.getElementById("checkout-form");
  if (form) {
    form.addEventListener("submit", handleOrderSubmit);
  }

  const areaSelect = document.getElementById("cust-area");
  if (areaSelect) {
    areaSelect.addEventListener("change", () => recalculateCheckoutSummary());
  }

  const applyVoucherBtn = document.getElementById("btn-apply-voucher");
  if (applyVoucherBtn) {
    applyVoucherBtn.addEventListener("click", () => handleApplyVoucher());
  }

  const saveAddrBtn = document.getElementById("btn-save-address-book");
  if (saveAddrBtn) {
    saveAddrBtn.addEventListener("click", saveCurrentToAddressBook);
  }

  // Bật/tắt ô chọn giờ hẹn
  document.querySelectorAll('input[name="delivery_mode"]').forEach(radio => {
    radio.addEventListener("change", (e) => {
      const timeInput = document.getElementById("scheduled-time-input");
      if (timeInput) {
        timeInput.disabled = e.target.value !== "scheduled";
      }
    });
  });

  // Sự kiện modal giá thay đổi (TC-29)
  const modalCancel = document.getElementById("modal-btn-cancel");
  const modalConfirm = document.getElementById("modal-btn-confirm");

  if (modalCancel) {
    modalCancel.addEventListener("click", () => {
      document.getElementById("price-change-modal").classList.remove("active");
      window.location.href = "cart.html";
    });
  }

  if (modalConfirm) {
    modalConfirm.addEventListener("click", async () => {
      document.getElementById("price-change-modal").classList.remove("active");
      await sendOrderRequest();
    });
  }
});

function getSavedAddresses() {
  try {
    const raw = localStorage.getItem(ADDRESS_BOOK_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed) && parsed.length > 0) return parsed;
    }
  } catch (e) {}
  return [
    {
      name: "Hoàng Nam",
      phone: "0912345678",
      area: "Nội thành",
      address: "Số 18 Ngõ 165 Cầu Giấy, Quận Cầu Giấy, Hà Nội",
    },
    {
      name: "Minh Quân",
      phone: "0987654321",
      area: "Thanh Xuân",
      address: "Tòa nhà Rivera Park, 69 Vũ Trọng Phụng, Thanh Xuân, Hà Nội",
    },
  ];
}

function initAddressBook() {
  const selectEl = document.getElementById("saved-address-select");
  if (!selectEl) return;
  const list = getSavedAddresses();
  selectEl.innerHTML = [
    `<option value="">📒 Chọn nhanh từ Sổ địa chỉ (${list.length})...</option>`,
    ...list.map((a, idx) => `<option value="${idx}">${escapeHtml(a.name)} - ${escapeHtml(a.phone)} (${escapeHtml(a.area)})</option>`)
  ].join("");

  selectEl.onchange = (e) => {
    const idx = e.target.value;
    if (idx === "") return;
    const chosen = getSavedAddresses()[parseInt(idx)];
    if (chosen) {
      document.getElementById("cust-name").value = chosen.name || "";
      document.getElementById("cust-phone").value = chosen.phone || "";
      document.getElementById("cust-address").value = chosen.address || "";
      if (chosen.area) {
        document.getElementById("cust-area").value = chosen.area;
      }
      recalculateCheckoutSummary();
      showToast("Đã điền thông tin từ sổ địa chỉ!", "info");
    }
  };
}

function saveCurrentToAddressBook() {
  const name = document.getElementById("cust-name").value.trim();
  const phone = document.getElementById("cust-phone").value.trim();
  const address = document.getElementById("cust-address").value.trim();
  const area = document.getElementById("cust-area").value;
  if (!name || !phone || !address) {
    showToast("Vui lòng nhập Họ tên, SĐT và Địa chỉ trước khi lưu vào sổ", "warning");
    return;
  }
  const list = getSavedAddresses();
  list.unshift({ name, phone, area, address });
  localStorage.setItem(ADDRESS_BOOK_KEY, JSON.stringify(list.slice(0, 10)));
  initAddressBook();
  showToast("Đã lưu địa chỉ vào Sổ địa chỉ!", "success");
}

function restoreSavedPaymentMethod() {
  const savedMethod = localStorage.getItem("nightfood_last_payment_method");
  if (savedMethod) {
    const radio = document.querySelector(`input[name="payment_method"][value="${savedMethod}"]`);
    if (radio) radio.checked = true;
  }
}

async function quickSelectVoucher(code) {
  const input = document.getElementById("voucher-code-input");
  if (input) {
    input.value = code;
    await handleApplyVoucher();
  }
}

async function handleApplyVoucher() {
  const input = document.getElementById("voucher-code-input");
  const fb = document.getElementById("voucher-feedback");
  const code = input ? input.value.trim().toUpperCase() : "";
  if (!code) {
    appliedVoucherCode = null;
    if (fb) fb.textContent = "";
    await recalculateCheckoutSummary();
    return;
  }

  try {
    const res = await api.post("/vouchers/check", {
      code,
      subtotal: currentSubtotal,
    });
    appliedVoucherCode = res.code;
    if (fb) {
      fb.style.color = "#4ade80";
      fb.textContent = `✓ ${res.message}`;
    }
    showToast(res.message, "success");
    await recalculateCheckoutSummary();
  } catch (err) {
    appliedVoucherCode = null;
    if (fb) {
      fb.style.color = "#f87171";
      fb.textContent = `✗ ${err.message}`;
    }
    showToast(err.message, "error");
    await recalculateCheckoutSummary();
  }
}

async function recalculateCheckoutSummary() {
  checkoutItems = CartStorage.getItems();

  if (!checkoutItems || checkoutItems.length === 0) {
    showToast("Giỏ hàng rỗng, đang chuyển về thực đơn...", "warning");
    setTimeout(() => {
      window.location.href = "dishes.html";
    }, 1200);
    return;
  }

  const itemsListEl = document.getElementById("checkout-items-list");
  const subtotalEl = document.getElementById("summary-subtotal");
  const shippingEl = document.getElementById("summary-shipping");
  const discountEl = document.getElementById("summary-discount");
  const totalEl = document.getElementById("summary-total");
  const area = document.getElementById("cust-area")?.value || "Nội thành";

  try {
    const calc = await api.post("/cart/calculate", {
      items: checkoutItems.map(it => ({
        dish_id: it.dish_id,
        quantity: it.quantity,
        dish_option_id: it.dish_option_id || null,
        selected_option_ids: it.selected_option_ids || null,
        note: it.note || null,
      })),
      area,
      voucher_code: appliedVoucherCode,
    });

    currentSubtotal = calc.subtotal;
    currentShippingFee = calc.shipping_fee;
    currentDiscount = calc.discount_amount;
    currentExpectedTotal = calc.total_amount;

    if (itemsListEl) {
      itemsListEl.innerHTML = (calc.items || []).map(it => `
        <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:12px; font-size:0.92rem; padding-bottom:8px; border-bottom:1px solid var(--border-subtle);">
          <div>
            <div style="font-weight:700; color:var(--text-main);">${escapeHtml(it.dish_name)}</div>
            ${it.option_name ? `<div style="color:var(--accent-primary); font-size:0.8rem;">+ ${escapeHtml(it.option_name)}</div>` : ''}
            ${it.note ? `<div style="color:var(--text-dim); font-size:0.78rem;">📝 ${escapeHtml(it.note)}</div>` : ''}
            <div style="color:var(--text-dim); font-size:0.82rem;">${formatVND(it.unit_price)} × ${it.quantity}</div>
          </div>
          <div style="font-weight:700; color:var(--accent-secondary);">${formatVND(it.line_total)}</div>
        </div>
      `).join("");
    }

    if (subtotalEl) subtotalEl.textContent = formatVND(currentSubtotal);
    if (shippingEl) shippingEl.textContent = currentShippingFee > 0 ? `+${formatVND(currentShippingFee)}` : "Miễn phí (0đ)";
    if (discountEl) discountEl.textContent = `-${formatVND(currentDiscount)}`;
    if (totalEl) totalEl.textContent = formatVND(currentExpectedTotal);
  } catch (err) {
    showToast("Không thể tính toán giỏ hàng: " + err.message, "error");
  }
}

async function handleOrderSubmit(e) {
  e.preventDefault();
  if (isSubmitting) return;

  clearErrors();

  const name = document.getElementById("cust-name").value.trim();
  const phone = document.getElementById("cust-phone").value.trim();
  const address = document.getElementById("cust-address").value.trim();
  const deliveryMode = document.querySelector('input[name="delivery_mode"]:checked')?.value || "immediate";
  const scheduledTime = document.getElementById("scheduled-time-input")?.value || "";

  let hasError = false;

  if (!name) {
    showFieldError("err-name", "Vui lòng nhập họ và tên người nhận");
    hasError = true;
  }

  const phoneRegex = /^0[0-9]{9}$/;
  if (!phone) {
    showFieldError("err-phone", "Vui lòng nhập số điện thoại");
    hasError = true;
  } else if (!phoneRegex.test(phone)) {
    showFieldError("err-phone", "Số điện thoại phải đúng 10 chữ số và bắt đầu bằng số 0 (TC-28)");
    hasError = true;
  }

  if (!address) {
    showFieldError("err-address", "Vui lòng nhập địa chỉ nhận hàng chi tiết");
    hasError = true;
  }

  if (deliveryMode === "scheduled") {
    if (!scheduledTime) {
      showFieldError("err-delivery-time", "Vui lòng chọn giờ hẹn giao");
      hasError = true;
    } else {
      const [h, m] = scheduledTime.split(":").map(Number);
      const validHour = h >= 18 || h < 2 || (h === 2 && m === 0);
      if (!validHour) {
        showFieldError("err-delivery-time", "Giờ hẹn giao phải nằm trong khung giờ mở cửa từ 18:00 đến 02:00 sáng");
        hasError = true;
      }
    }
  }

  if (hasError) return;

  await sendOrderRequest();
}

async function sendOrderRequest() {
  const submitBtn = document.getElementById("btn-submit-order");
  const name = document.getElementById("cust-name").value.trim();
  const phone = document.getElementById("cust-phone").value.trim();
  const email = document.getElementById("cust-email")?.value.trim() || null;
  const area = document.getElementById("cust-area")?.value || "Nội thành";
  const address = document.getElementById("cust-address").value.trim();
  const note = document.getElementById("cust-note").value.trim();
  const paymentMethod = document.querySelector('input[name="payment_method"]:checked')?.value || "COD";
  const deliveryMode = document.querySelector('input[name="delivery_mode"]:checked')?.value || "immediate";
  const scheduledTime = document.getElementById("scheduled-time-input")?.value || "";
  const desiredTime = deliveryMode === "scheduled" ? `Hẹn giờ ${scheduledTime}` : "Giao ngay";

  // Lưu lựa chọn thanh toán và SĐT cho lần sau (T3D28BB)
  localStorage.setItem("nightfood_last_payment_method", paymentMethod);
  localStorage.setItem("nightfood_last_phone", phone);
  localStorage.setItem("nightfood_last_name", name);

  const payload = {
    customer_name: name,
    phone: phone,
    customer_email: email,
    address: address,
    area: area,
    note: note || null,
    desired_delivery_time: desiredTime,
    payment_method: paymentMethod,
    voucher_code: appliedVoucherCode,
    guest_token: CartStorage.getGuestToken(),
    expected_total: currentExpectedTotal,
    items: checkoutItems.map(it => ({
      dish_id: it.dish_id,
      quantity: it.quantity,
      dish_option_id: it.dish_option_id || null,
      selected_option_ids: it.selected_option_ids || null,
      note: it.note || null,
    })),
  };

  try {
    isSubmitting = true;
    submitBtn.disabled = true;
    submitBtn.textContent = "⏳ Đang gửi đơn hàng...";

    const res = await api.post("/orders", payload);

    CartStorage.clear();
    showToast("Đặt hàng thành công!", "success");

    setTimeout(() => {
      window.location.href = `order-success.html?code=${res.order_code}&total=${res.total_amount}&name=${encodeURIComponent(name)}&phone=${phone}&method=${encodeURIComponent(paymentMethod)}`;
    }, 500);

  } catch (err) {
    isSubmitting = false;
    submitBtn.disabled = false;
    submitBtn.textContent = "✅ Đặt Món Ngay";

    if (err.status === 409 && (err.code === "PRICE_CHANGED" || (err.data && err.data.error && err.data.error.code === "PRICE_CHANGED"))) {
      const details = err.data.error.details;
      currentExpectedTotal = details.total_amount;
      const modalNewTotal = document.getElementById("modal-new-total");
      if (modalNewTotal) modalNewTotal.textContent = formatVND(details.total_amount);
      document.getElementById("summary-total").textContent = formatVND(details.total_amount);
      document.getElementById("price-change-modal").classList.add("active");
      return;
    }

    if (err.status === 409 && (err.code === "STORE_CLOSED" || (err.data && err.data.error && err.data.error.code === "STORE_CLOSED"))) {
      showToast(err.message, "error");
      alert(err.message);
      return;
    }

    showToast(err.message || "Không thể đặt hàng, vui lòng thử lại", "error");
  }
}

function showFieldError(feedbackId, msg) {
  const fb = document.getElementById(feedbackId);
  if (fb) fb.textContent = msg;
}

function clearErrors() {
  document.querySelectorAll(".invalid-feedback").forEach(el => el.textContent = "");
}
