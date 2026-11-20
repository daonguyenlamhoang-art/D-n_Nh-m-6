// Logic Trang Đặt hàng Checkout (FR-06, BR-05, BR-17, TC-09..13, TC-28, TC-29, TC-31, TC-39)

let checkoutItems = [];
let dishDetailsMap = {};
let currentExpectedTotal = 0;
let isSubmitting = false;

document.addEventListener("DOMContentLoaded", async () => {
  await loadCheckoutData();

  const form = document.getElementById("checkout-form");
  if (form) {
    form.addEventListener("submit", handleOrderSubmit);
  }

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

async function loadCheckoutData() {
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
  const totalEl = document.getElementById("summary-total");

  try {
    const ids = checkoutItems.map(it => it.dish_id).join(",");
    const dishes = await api.get("/dishes", { ids });

    dishDetailsMap = {};
    dishes.forEach(d => {
      dishDetailsMap[d.id] = d;
    });

    currentExpectedTotal = 0;
    let listHtml = "";

    checkoutItems.forEach(it => {
      const dish = dishDetailsMap[it.dish_id];
      if (dish) {
        const itemTotal = dish.price * it.quantity;
        currentExpectedTotal += itemTotal;
        listHtml += `
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; font-size:0.92rem;">
            <div>
              <div style="font-weight:600; color:var(--text-main);">${escapeHtml(dish.name)}</div>
              <div style="color:var(--text-dim); font-size:0.82rem;">${formatVND(dish.price)} x ${it.quantity}</div>
            </div>
            <div style="font-weight:700; color:var(--accent-secondary);">${formatVND(itemTotal)}</div>
          </div>
        `;
      }
    });

    if (itemsListEl) itemsListEl.innerHTML = listHtml;
    if (subtotalEl) subtotalEl.textContent = formatVND(currentExpectedTotal);
    if (totalEl) totalEl.textContent = formatVND(currentExpectedTotal);

  } catch (err) {
    showToast("Không thể tải thông tin món ăn trong giỏ", "error");
  }
}

async function handleOrderSubmit(e) {
  e.preventDefault();
  if (isSubmitting) return;

  // Xóa thông báo lỗi cũ
  clearErrors();

  const nameInput = document.getElementById("cust-name");
  const phoneInput = document.getElementById("cust-phone");
  const addrInput = document.getElementById("cust-address");

  const name = nameInput.value.trim();
  const phone = phoneInput.value.trim();
  const address = addrInput.value.trim();

  let hasError = false;

  if (!name) {
    showFieldError("err-name", "nameInput", "Vui lòng nhập họ và tên người nhận");
    hasError = true;
  }

  const phoneRegex = /^0[0-9]{9}$/;
  if (!phone) {
    showFieldError("err-phone", "phoneInput", "Vui lòng nhập số điện thoại");
    hasError = true;
  } else if (!phoneRegex.test(phone)) {
    showFieldError("err-phone", "phoneInput", "Số điện thoại phải đúng 10 chữ số và bắt đầu bằng số 0 (TC-28)");
    hasError = true;
  }

  if (!address) {
    showFieldError("err-address", "addrInput", "Vui lòng nhập địa chỉ nhận hàng chi tiết");
    hasError = true;
  }

  if (hasError) return;

  await sendOrderRequest();
}

async function sendOrderRequest() {
  const submitBtn = document.getElementById("btn-submit-order");
  const name = document.getElementById("cust-name").value.trim();
  const phone = document.getElementById("cust-phone").value.trim();
  const address = document.getElementById("cust-address").value.trim();
  const note = document.getElementById("cust-note").value.trim();

  const payload = {
    customer_name: name,
    phone: phone,
    address: address,
    note: note || null,
    expected_total: currentExpectedTotal,
    items: checkoutItems.map(it => ({
      dish_id: it.dish_id,
      quantity: it.quantity,
      dish_option_id: it.dish_option_id || null,
    })),
  };

  try {
    isSubmitting = true;
    submitBtn.disabled = true;
    submitBtn.textContent = "⏳ Đang gửi đơn hàng...";

    const res = await api.post("/orders", payload);

    // Thành công -> xóa giỏ hàng và chuyển trang
    CartStorage.clear();
    showToast("Đặt hàng thành công!", "success");

    setTimeout(() => {
      window.location.href = `order-success.html?code=${res.order_code}&total=${res.total_amount}&name=${encodeURIComponent(name)}&phone=${phone}`;
    }, 500);

  } catch (err) {
    isSubmitting = false;
    submitBtn.disabled = false;
    submitBtn.textContent = "✅ Xác Nhận Đặt Hàng Ngay";

    // Xử lý mã lỗi PRICE_CHANGED (HTTP 409, TC-29)
    if (err.status === 409 && (err.code === "PRICE_CHANGED" || (err.data && err.data.error && err.data.error.code === "PRICE_CHANGED"))) {
      const details = err.data.error.details;
      currentExpectedTotal = details.total_amount;

      const modalPriceDetails = document.getElementById("modal-price-details");
      const modalNewTotal = document.getElementById("modal-new-total");

      if (modalPriceDetails && details.items) {
        modalPriceDetails.innerHTML = details.items.map(it => {
          const dish = dishDetailsMap[it.dish_id];
          return `
            <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
              <span>${escapeHtml(dish ? dish.name : 'Món #' + it.dish_id)} x ${it.quantity}:</span>
              <strong style="color:var(--accent-secondary);">${formatVND(it.unit_price * it.quantity)}</strong>
            </div>
          `;
        }).join("");
      }

      if (modalNewTotal) {
        modalNewTotal.textContent = formatVND(details.total_amount);
      }

      // Cập nhật lại số tiền trên màn hình checkout
      document.getElementById("summary-total").textContent = formatVND(details.total_amount);

      // Hiển thị modal
      document.getElementById("price-change-modal").classList.add("active");
      return;
    }

    // Xử lý đóng cửa (STORE_CLOSED)
    if (err.status === 409 && (err.code === "STORE_CLOSED" || (err.data && err.data.error && err.data.error.code === "STORE_CLOSED"))) {
      showToast(err.message, "error");
      alert(err.message);
      return;
    }

    // Các lỗi khác
    showToast(err.message || "Không thể đặt hàng, vui lòng thử lại", "error");
  }
}

function showFieldError(feedbackId, inputId, msg) {
  const fb = document.getElementById(feedbackId);
  if (fb) fb.textContent = msg;
}

function clearErrors() {
  document.querySelectorAll(".invalid-feedback").forEach(el => el.textContent = "");
}
