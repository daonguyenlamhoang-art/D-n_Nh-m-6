// Quản lý giỏ hàng (localStorage + đồng bộ tuỳ chọn & ghi chú - T3D2887, T3D25F6)

const CART_KEY = "nightfood_cart";
const GUEST_TOKEN_KEY = "nightfood_guest_token";

const CartStorage = {
  getGuestToken() {
    let tok = localStorage.getItem(GUEST_TOKEN_KEY);
    if (!tok) {
      tok = "nf_" + Math.random().toString(36).slice(2, 10) + "_" + Date.now().toString(36);
      localStorage.setItem(GUEST_TOKEN_KEY, tok);
    }
    return tok;
  },

  _normalizeOptionIds(dishOptionId, selectedOptionIds) {
    let ids = [];
    if (Array.isArray(selectedOptionIds) && selectedOptionIds.length > 0) {
      ids = [...new Set(selectedOptionIds.map(Number).filter(Boolean))].sort((a, b) => a - b);
    } else if (dishOptionId) {
      ids = [Number(dishOptionId)];
    }
    return ids;
  },

  getItems() {
    try {
      const raw = localStorage.getItem(CART_KEY);
      if (!raw) return [];
      const items = JSON.parse(raw);
      if (!Array.isArray(items)) return [];
      return items.filter(
        (it) => it && typeof it.dish_id === "number" && typeof it.quantity === "number" && it.quantity > 0
      );
    } catch (e) {
      console.warn("Giỏ hàng localStorage lỗi, khởi tạo lại giỏ rỗng:", e);
      return [];
    }
  },

  saveItems(items) {
    localStorage.setItem(CART_KEY, JSON.stringify(items));
    window.dispatchEvent(new CustomEvent("nightfood_cart_changed"));
  },

  addItem(dishId, quantity = 1, dishOptionId = null, note = "", selectedOptionIds = null, optionName = null) {
    let items = this.getItems();
    const normOpts = this._normalizeOptionIds(dishOptionId, selectedOptionIds);
    const normOptsKey = JSON.stringify(normOpts);
    const normNote = (note || "").trim();

    // Cùng món nhưng khác tuỳ chọn hoặc ghi chú là dòng riêng; trùng hoàn toàn thì cộng dồn
    const existingIndex = items.findIndex((it) => {
      const itOpts = this._normalizeOptionIds(it.dish_option_id, it.selected_option_ids);
      const itNote = (it.note || "").trim();
      return it.dish_id === dishId && JSON.stringify(itOpts) === normOptsKey && itNote === normNote;
    });

    if (existingIndex > -1) {
      let newQty = items[existingIndex].quantity + quantity;
      if (newQty > 99) {
        newQty = 99;
        if (typeof showToast === "function") {
          showToast("Số lượng mỗi dòng tối đa là 99", "warning");
        }
      }
      items[existingIndex].quantity = newQty;
    } else {
      let validQty = Math.min(Math.max(1, quantity), 99);
      items.push({
        dish_id: dishId,
        quantity: validQty,
        dish_option_id: normOpts[0] || null,
        selected_option_ids: normOpts,
        option_name: optionName || null,
        note: normNote || null,
      });
    }

    this.saveItems(items);
    if (typeof showToast === "function") {
      showToast("Đã thêm món vào giỏ hàng!", "success");
    }
  },

  updateQuantityByIndex(index, quantity) {
    let items = this.getItems();
    if (index < 0 || index >= items.length) return;
    if (quantity <= 0) {
      items.splice(index, 1);
    } else {
      items[index].quantity = Math.min(Math.max(1, quantity), 99);
    }
    this.saveItems(items);
  },

  updateNoteByIndex(index, newNote) {
    let items = this.getItems();
    if (index < 0 || index >= items.length) return;
    items[index].note = (newNote || "").trim() || null;
    this.saveItems(items);
    if (typeof showToast === "function") {
      showToast("Đã lưu ghi chú món ăn", "info");
    }
  },

  removeItemByIndex(index) {
    let items = this.getItems();
    if (index < 0 || index >= items.length) return;
    items.splice(index, 1);
    this.saveItems(items);
    if (typeof showToast === "function") {
      showToast("Đã xóa món khỏi giỏ", "info");
    }
  },

  updateQuantity(dishId, quantity) {
    let items = this.getItems();
    if (quantity <= 0) {
      items = items.filter((it) => it.dish_id !== dishId);
    } else {
      const it = items.find((x) => x.dish_id === dishId);
      if (it) {
        it.quantity = Math.min(Math.max(1, quantity), 99);
      }
    }
    this.saveItems(items);
  },

  removeItem(dishId) {
    let items = this.getItems().filter((it) => it.dish_id !== dishId);
    this.saveItems(items);
    if (typeof showToast === "function") {
      showToast("Đã xóa món khỏi giỏ", "info");
    }
  },

  clear() {
    localStorage.removeItem(CART_KEY);
    window.dispatchEvent(new CustomEvent("nightfood_cart_changed"));
  },

  getTotalCount() {
    return this.getItems().reduce((sum, it) => sum + (it.quantity || 0), 0);
  },
};
