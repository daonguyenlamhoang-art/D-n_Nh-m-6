// Logic Trang chủ NightFood & Menu theo danh mục (T3D24E7, T3D2587, T3D2E96)

document.addEventListener("DOMContentLoaded", async () => {
  await loadHomeMenu();
  renderRecentlyViewedSection();

  const clearBtn = document.getElementById("btn-clear-recent");
  if (clearBtn) {
    clearBtn.addEventListener("click", () => {
      localStorage.removeItem("nightfood_recently_viewed");
      renderRecentlyViewedSection();
    });
  }
});

function renderRecentlyViewedSection() {
  const section = document.getElementById("recently-viewed-section");
  const grid = document.getElementById("recently-viewed-grid");
  if (!section || !grid) return;

  try {
    const list = JSON.parse(localStorage.getItem("nightfood_recently_viewed") || "[]");
    if (!Array.isArray(list) || list.length === 0) {
      section.style.display = "none";
      return;
    }
    section.style.display = "block";
    grid.innerHTML = list.slice(0, 3).map(d => renderFigmaDishCard({
      ...d,
      is_available: true,
      status: "AVAILABLE",
    })).join("");
    bindDishCardActions();
  } catch (e) {
    section.style.display = "none";
  }
}

async function loadHomeMenu() {
  const featuredContainer = document.getElementById("featured-dishes-grid");
  const comboContainer = document.getElementById("combo-dishes-grid");
  const navContainer = document.getElementById("home-category-scroll-nav");
  const sectionsContainer = document.getElementById("home-categories-sections");

  try {
    const menuData = await api.get("/dishes/menu");
    const categories = menuData.categories || [];
    const featured = menuData.featured_dishes || [];
    const bestsellers = menuData.bestseller_dishes || [];

    // 1. Render Món nổi bật
    const displayFeatured = featured.length > 0 ? featured.slice(0, 6) : bestsellers.slice(0, 6);
    if (featuredContainer) {
      featuredContainer.innerHTML = displayFeatured.map(d => renderFigmaDishCard(d)).join("");
    }

    // 2. Render thanh danh mục dính trên cùng (cuộn mượt tới từng danh mục khi bấm)
    if (navContainer && categories.length > 0) {
      const navHtml = [
        `<button class="category-tab active" data-target="featured-section">🔥 Món Nổi Bật</button>`,
        ...categories.map(c => `
          <button class="category-tab" data-target="cat-section-${c.id}">${escapeHtml(c.name)} (${c.dish_count})</button>
        `)
      ].join("");
      navContainer.innerHTML = navHtml;

      navContainer.querySelectorAll(".category-tab").forEach(btn => {
        btn.addEventListener("click", () => {
          navContainer.querySelectorAll(".category-tab").forEach(b => b.classList.remove("active"));
          btn.classList.add("active");
          const targetId = btn.getAttribute("data-target");
          const targetEl = document.getElementById(targetId);
          if (targetEl) {
            targetEl.scrollIntoView({ behavior: "smooth", block: "start" });
          }
        });
      });
    }

    // 3. Render từng khu vực danh mục trên trang chủ
    if (sectionsContainer && categories.length > 0) {
      sectionsContainer.innerHTML = categories.map(cat => `
        <section id="cat-section-${cat.id}" style="margin-bottom: 44px; scroll-margin-top: 135px;">
          <div class="section-header">
            <h2 class="section-title">
              <span>🍽️ ${escapeHtml(cat.name)}</span>
              <span class="badge-tag">${cat.dish_count} món</span>
            </h2>
            <a href="dishes.html?category_id=${cat.id}" class="btn btn-secondary" style="font-size:0.85rem; padding:6px 14px;">
              Xem trong bộ lọc →
            </a>
          </div>
          <div class="dish-grid-3">
            ${(cat.dishes || []).map(d => renderFigmaDishCard(d, cat.id === 5)).join("")}
          </div>
        </section>
      `).join("");
    }

    // 4. Render mục Combo ăn đêm siêu hời
    const comboCat = categories.find(c => c.id === 5);
    const combos = comboCat ? comboCat.dishes.slice(0, 3) : [];
    if (comboContainer && combos.length > 0) {
      comboContainer.innerHTML = combos.map(d => renderFigmaDishCard(d, true)).join("");
    }

    bindDishCardActions();
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

function isFavoriteDish(dishId) {
  try {
    const favs = JSON.parse(localStorage.getItem("nightfood_favorites") || "[]");
    return Array.isArray(favs) && favs.includes(dishId);
  } catch (e) {
    return false;
  }
}

function toggleFavoriteDish(dishId, btnEl) {
  try {
    let favs = JSON.parse(localStorage.getItem("nightfood_favorites") || "[]");
    if (!Array.isArray(favs)) favs = [];
    if (favs.includes(dishId)) {
      favs = favs.filter(id => id !== dishId);
      if (btnEl) {
        btnEl.classList.remove("active");
        btnEl.textContent = "🤍";
      }
      showToast("Đã bỏ khỏi danh sách món yêu thích", "info");
    } else {
      favs.push(dishId);
      if (btnEl) {
        btnEl.classList.add("active");
        btnEl.textContent = "❤️";
      }
      showToast("Đã lưu vào món yêu thích ❤️", "success");
    }
    localStorage.setItem("nightfood_favorites", JSON.stringify(favs));
    window.dispatchEvent(new CustomEvent("nightfood_favorites_changed"));
  } catch (e) {
    console.warn(e);
  }
}

function renderFigmaDishCard(dish, isCombo = false) {
  const defaultImg = "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=500&auto=format&fit=crop&q=60";
  const imgUrl = dish.image_url ? escapeHtml(dish.image_url) : defaultImg;
  const isAvailable = dish.is_available && dish.status !== "OUT_OF_STOCK";
  const categoryBadge = isCombo || dish.is_combo ? "Combo Tiết Kiệm" : (dish.category_name || "Món Hot Đêm");
  const isFav = isFavoriteDish(dish.id);
  const ratingText = dish.avg_rating ? `⭐ ${dish.avg_rating}` : "⭐ 5.0";

  return `
    <div class="dish-card ${!isAvailable ? 'out-of-stock' : ''}" data-dish-id="${dish.id}">
      <div class="dish-card-img-wrapper">
        <button type="button" class="btn-fav-heart ${isFav ? 'active' : ''}" data-fav-id="${dish.id}" title="Yêu thích">
          ${isFav ? '❤️' : '🤍'}
        </button>
        <img src="${imgUrl}" alt="${escapeHtml(dish.name)}" class="dish-card-img" loading="lazy" onerror="this.src='${defaultImg}'">
        <span class="dish-card-badge">${escapeHtml(categoryBadge)} · ${ratingText}</span>
      </div>
      <div class="dish-card-body">
        <h3 class="dish-card-title">${escapeHtml(dish.name)}</h3>
        <p class="dish-card-desc">${escapeHtml(dish.description || 'Chế biến nóng sốt ngay sau khi đặt hàng.')}</p>
        <div class="dish-card-footer">
          <div class="dish-price">${formatVND(dish.price)}</div>
          <div style="display:flex; gap:8px;">
            <a href="product-detail.html?id=${dish.id}" class="btn btn-secondary" style="padding:6px 12px; font-size:0.82rem;">Chi tiết</a>
            <button 
              type="button"
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

function bindDishCardActions() {
  document.querySelectorAll(".btn-add-cart").forEach(btn => {
    btn.onclick = (e) => {
      const dishId = parseInt(e.currentTarget.getAttribute("data-id"));
      CartStorage.addItem(dishId, 1);
    };
  });

  document.querySelectorAll(".btn-fav-heart").forEach(btn => {
    btn.onclick = (e) => {
      e.preventDefault();
      e.stopPropagation();
      const dishId = parseInt(e.currentTarget.getAttribute("data-fav-id"));
      toggleFavoriteDish(dishId, e.currentTarget);
    };
  });
}
