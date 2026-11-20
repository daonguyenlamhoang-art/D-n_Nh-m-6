// Logic Trang chủ NightFood theo chuẩn Figma Frame 1

document.addEventListener("DOMContentLoaded", async () => {
  await loadHomeDishes();
});

async function loadHomeDishes() {
  const featuredContainer = document.getElementById("featured-dishes-grid");
  const comboContainer = document.getElementById("combo-dishes-grid");

  try {
    const dishes = await api.get("/dishes");
    if (!dishes || dishes.length === 0) {
      if (featuredContainer) {
        featuredContainer.innerHTML = `
          <div style="grid-column: 1 / -1; text-align:center; padding: 40px; color:var(--text-dim);">
            Hiện tại chưa có món ăn nào trong thực đơn.
          </div>
        `;
      }
      return;
    }

    // 1. Lọc 3 món bán chạy (không phải combo) cho mục "Món Bán Chạy Nhất"
    const hotDishes = dishes.filter(d => d.category_id !== 5).slice(0, 3);
    if (featuredContainer) {
      featuredContainer.innerHTML = hotDishes.map(d => renderFigmaDishCard(d)).join("");
    }

    // 2. Lọc 3 Combo cho mục "Combo Ăn Đêm Siêu Hời"
    const combos = dishes.filter(d => d.category_id === 5).slice(0, 3);
    if (comboContainer) {
      comboContainer.innerHTML = combos.map(d => renderFigmaDishCard(d, true)).join("");
    }

    // Gắn sự kiện Thêm vào giỏ
    document.querySelectorAll(".btn-add-cart").forEach(btn => {
      btn.addEventListener("click", (e) => {
        const dishId = parseInt(e.target.getAttribute("data-id"));
        CartStorage.addItem(dishId, 1);
      });
    });

  } catch (err) {
    if (featuredContainer) {
      featuredContainer.innerHTML = `
        <div style="grid-column: 1 / -1; text-align:center; padding: 40px; color:var(--danger);">
          Không thể tải thực đơn: ${escapeHtml(err.message)}
        </div>
      `;
    }
  }
}

function renderFigmaDishCard(dish, isCombo = false) {
  const defaultImg = "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=500&auto=format&fit=crop&q=60";
  const imgUrl = dish.image_url ? escapeHtml(dish.image_url) : defaultImg;
  const isAvailable = dish.is_available;
  const categoryBadge = isCombo ? "Combo Tiết Kiệm" : (dish.category_name || "Món Hot Đêm");

  return `
    <div class="dish-card">
      <div class="dish-card-img-wrapper">
        <img src="${imgUrl}" alt="${escapeHtml(dish.name)}" class="dish-card-img" loading="lazy" onerror="this.src='${defaultImg}'">
        <span class="dish-card-badge">${escapeHtml(categoryBadge)}</span>
      </div>
      <div class="dish-card-body">
        <h3 class="dish-card-title">${escapeHtml(dish.name)}</h3>
        <p class="dish-card-desc">${escapeHtml(dish.description || 'Chế biến nóng sốt ngay sau khi đặt hàng.')}</p>
        <div class="dish-card-footer">
          <div class="dish-price">${formatVND(dish.price)}</div>
          <div style="display:flex; gap:8px;">
            <a href="product-detail.html?id=${dish.id}" class="btn btn-secondary" style="padding:6px 12px; font-size:0.82rem;">Chi tiết</a>
            <button 
              class="btn-add-cart" 
              data-id="${dish.id}" 
              ${!isAvailable ? 'disabled title="Món này hiện đã hết hàng"' : ''}>
              ${isAvailable ? '+ Thêm' : 'Hết món'}
            </button>
          </div>
        </div>
      </div>
    </div>
  `;
}
