// Quản lý giỏ hàng trong localStorage (FR-04, FR-05, BR-02, BR-03, TC-05..08, TC-27, TC-38)

const CART_KEY = "nightfood_cart";

const CartStorage = {
  getItems() {
    try {
      const raw = localStorage.getItem(CART_KEY);
      if (!raw) return [];
      const items = JSON.parse(raw);
      if (!Array.isArray(items)) return [];
      // Lọc dữ liệu hợp lệ (TC-38)
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

  addItem(dishId, quantity = 1, dishOptionId = null) {
    let items = this.getItems();
    const existingIndex = items.findIndex((it) => it.dish_id === dishId);

    if (existingIndex > -1) {
      let newQty = items[existingIndex].quantity + quantity;
      if (newQty > 99) {
        newQty = 99;
        if (typeof showToast === "function") {
          showToast("Số lượng mỗi món tối đa là 99", "warning");
        }
      }
      items[existingIndex].quantity = newQty;
    } else {
      let validQty = Math.min(Math.max(1, quantity), 99);
      items.push({
        dish_id: dishId,
        quantity: validQty,
        dish_option_id: dishOptionId,
      });
    }

    this.saveItems(items);
    if (typeof showToast === "function") {
      showToast("Đã thêm món vào giỏ hàng!", "success");
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
