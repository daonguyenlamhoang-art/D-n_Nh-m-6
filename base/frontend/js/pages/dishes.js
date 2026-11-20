// Logic Thực đơn món ăn: Tìm kiếm có gợi ý debounce, Bộ lọc, Sắp xếp & Phân trang (T3D251C, T3D2354)

let currentCategoryId = "";
let currentSearch = "";
let currentMinPrice = null;
let currentMaxPrice = null;
let currentAvailableOnly = false;
let currentSortBy = "";
let currentPage = 1;
const PAGE_SIZE = 9;
let searchTimeout = null;

document.addEventListener("DOMContentLoaded", async () => {
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.get("category_id")) {
    currentCategoryId = urlParams.get("category_id");
  }

  await loadCategories();
  await loadDishes();

  const searchInput = document.getElementById("search-input");
  const suggestionsBox = document.getElementById("search-suggestions");

  if (searchInput) {
    searchInput.addEventListener("input", (e) => {
      clearTimeout(searchTimeout);
      const val = e.target.value.trim();
      searchTimeout = setTimeout(async () => {
        currentSearch = val;
        currentPage = 1;
        await loadDishes();
        await renderSearchSuggestions(val);
      }, 300);
    });

    document.addEventListener("click", (e) => {
      if (suggestionsBox && !searchInput.contains(e.target) && !suggestionsBox.contains(e.target)) {
        suggestionsBox.classList.remove("active");
      }
    });
  }

  const priceSelect = document.getElementById("filter-price-range");
  if (priceSelect) {
    priceSelect.addEventListener("change", (e) => {
      const val = e.target.value;
      if (!val) {
        currentMinPrice = null;
        currentMaxPrice = null;
      } else {
        const [minP, maxP] = val.split("-").map(Number);
        currentMinPrice = minP;
        currentMaxPrice = maxP;
      }
      currentPage = 1;
      loadDishes();
    });
  }

  const availCheck = document.getElementById("filter-available-only");
  if (availCheck) {
    availCheck.addEventListener("change", (e) => {
      currentAvailableOnly = e.target.checked;
      currentPage = 1;
      loadDishes();
    });
  }

  const sortSelect = document.getElementById("filter-sort-by");
  if (sortSelect) {
    sortSelect.addEventListener("change", (e) => {
      currentSortBy = e.target.value;
      currentPage = 1;
      loadDishes();
    });
  }
});

async function renderSearchSuggestions(keyword) {
  const suggestionsBox = document.getElementById("search-suggestions");
  if (!suggestionsBox) return;
  if (!keyword || keyword.length < 1) {
    suggestionsBox.classList.remove("active");
    suggestionsBox.innerHTML = "";
    return;
  }

  try {
    const res = await api.get("/dishes/search", { q: keyword, page: 1, page_size: 5 });
    const items = res.items || [];
    if (items.length === 0) {
      suggestionsBox.innerHTML = `<div style="padding:10px 14px; color:var(--text-dim); font-size:0.85rem;">Không có gợi ý cho "${escapeHtml(keyword)}"</div>`;
      suggestionsBox.classList.add("active");
      return;
    }

    const defaultImg = "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=500&auto=format&fit=crop&q=60";
    suggestionsBox.innerHTML = items.map(d => `
      <a href="product-detail.html?id=${d.id}" class="suggestion-item">
        <img src="${escapeHtml(d.image_url || defaultImg)}" alt="${escapeHtml(d.name)}" style="width:40px; height:40px; border-radius:6px; object-fit:cover;" onerror="this.src='${defaultImg}'">
        <div style="flex:1;">
          <div style="font-weight:700; font-size:0.88rem; color:var(--text-main);">${escapeHtml(d.name)}</div>
          <div style="font-size:0.78rem; color:var(--accent-secondary); font-weight:700;">${formatVND(d.price)}</div>
        </div>
      </a>
    `).join("");
    suggestionsBox.classList.add("active");
  } catch (e) {
    suggestionsBox.classList.remove("active");
  }
}

async function loadCategories() {
  const tabsContainer = document.getElementById("category-tabs-container");
  if (!tabsContainer) return;

  try {
    const categories = await api.get("/categories");
    const tabsHtml = [
      `<button class="category-tab ${!currentCategoryId ? 'active' : ''}" data-category-id="">Tất cả món</button>`,
      ...categories.map(c => `
        <button class="category-tab ${String(currentCategoryId) === String(c.id) ? 'active' : ''}" data-category-id="${c.id}">
          ${escapeHtml(c.name)} ${c.dish_count !== undefined ? `(${c.dish_count})` : ''}
        </button>
      `)
    ].join("");

    tabsContainer.innerHTML = tabsHtml;

    tabsContainer.querySelectorAll(".category-tab").forEach(tab => {
      tab.addEventListener("click", (e) => {
        tabsContainer.querySelectorAll(".category-tab").forEach(t => t.classList.remove("active"));
        e.currentTarget.classList.add("active");
        currentCategoryId = e.currentTarget.getAttribute("data-category-id");
        currentPage = 1;
        loadDishes();
      });
    });
  } catch (err) {
    console.error("Lỗi tải danh mục:", err);
  }
}

async function loadDishes() {
  const grid = document.getElementById("dishes-grid");
  const pagEl = document.getElementById("dishes-pagination");
  if (!grid) return;

  grid.innerHTML = `
    <div style="grid-column: 1 / -1; text-align:center; padding: 40px; color:var(--text-dim);">
      ⏳ Đang tìm món ngon đêm nay...
    </div>
  `;

  try {
    const params = { page: currentPage, page_size: PAGE_SIZE };
    if (currentCategoryId) params.category_id = currentCategoryId;
    if (currentSearch) params.q = currentSearch;
    if (currentMinPrice !== null) params.min_price = currentMinPrice;
    if (currentMaxPrice !== null) params.max_price = currentMaxPrice;
    if (currentAvailableOnly) params.available_only = true;
    if (currentSortBy) params.sort_by = currentSortBy;

    const res = await api.get("/dishes/search", params);
    const dishes = res.items || [];

    if (dishes.length === 0) {
      grid.innerHTML = `
        <div style="grid-column: 1 / -1; text-align:center; padding: 60px 20px;">
          <div style="font-size:3rem; margin-bottom:12px;">🔍</div>
          <h3 style="color:var(--text-main); margin-bottom:6px;">Không tìm thấy món ăn nào phù hợp</h3>
          <p style="color:var(--text-muted); font-size:0.9rem;">Thử tìm kiếm với từ khóa khác hoặc đặt lại bộ lọc bạn nhé!</p>
        </div>
      `;
      if (pagEl) pagEl.innerHTML = "";
      return;
    }

    grid.innerHTML = dishes.map(dish => renderDishCard(dish)).join("");
    renderPagination(res.page, res.total_pages);

    grid.querySelectorAll(".btn-add-cart").forEach(btn => {
      btn.addEventListener("click", (e) => {
        const dishId = parseInt(e.currentTarget.getAttribute("data-id"));
        CartStorage.addItem(dishId, 1);
      });
    });

    grid.querySelectorAll(".btn-fav-heart").forEach(btn => {
      btn.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();
        const dishId = parseInt(e.currentTarget.getAttribute("data-fav-id"));
        toggleDishFavorite(dishId, e.currentTarget);
      });
    });
  } catch (err) {
    grid.innerHTML = `
      <div style="grid-column: 1 / -1; text-align:center; padding: 40px; color:var(--danger);">
        ⚠️ Không thể tải danh sách món: ${escapeHtml(err.message)}
      </div>
    `;
  }
}

function renderPagination(page, totalPages) {
  const pagEl = document.getElementById("dishes-pagination");
  if (!pagEl) return;
  if (!totalPages || totalPages <= 1) {
    pagEl.innerHTML = "";
    return;
  }

  let html = "";
  for (let p = 1; p <= totalPages; p++) {
    html += `
      <button type="button" class="btn ${p === page ? 'btn-primary' : 'btn-secondary'}" style="padding:6px 14px; font-size:0.88rem;" onclick="goToDishPage(${p})">
        ${p}
      </button>
    `;
  }
  pagEl.innerHTML = html;
}

function goToDishPage(p) {
  currentPage = p;
  loadDishes();
  window.scrollTo({ top: 180, behavior: "smooth" });
}

function isDishFavorite(dishId) {
  try {
    const favs = JSON.parse(localStorage.getItem("nightfood_favorites") || "[]");
    return Array.isArray(favs) && favs.includes(dishId);
  } catch (e) {
    return false;
  }
}

function toggleDishFavorite(dishId, btnEl) {
  try {
    let favs = JSON.parse(localStorage.getItem("nightfood_favorites") || "[]");
    if (!Array.isArray(favs)) favs = [];
    if (favs.includes(dishId)) {
      favs = favs.filter(id => id !== dishId);
      btnEl.classList.remove("active");
      btnEl.textContent = "🤍";
      showToast("Đã bỏ khỏi món yêu thích", "info");
    } else {
      favs.push(dishId);
      btnEl.classList.add("active");
      btnEl.textContent = "❤️";
      showToast("Đã lưu vào món yêu thích ❤️", "success");
    }
    localStorage.setItem("nightfood_favorites", JSON.stringify(favs));
  } catch (e) {}
}

function renderDishCard(dish) {
  const defaultImg = "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=500&auto=format&fit=crop&q=60";
  const imgUrl = dish.image_url ? escapeHtml(dish.image_url) : defaultImg;
  const isAvailable = dish.is_available && dish.status !== "OUT_OF_STOCK";
  const categoryLabel = dish.category_name ? escapeHtml(dish.category_name) : "";
  const ratingText = dish.avg_rating ? `⭐ ${dish.avg_rating}` : "⭐ 5.0";
  const isFav = isDishFavorite(dish.id);

  return `
    <div class="dish-card ${!isAvailable ? 'out-of-stock' : ''}">
      <div class="dish-card-img-wrapper">
        <button type="button" class="btn-fav-heart ${isFav ? 'active' : ''}" data-fav-id="${dish.id}" title="Lưu món yêu thích">
          ${isFav ? '❤️' : '🤍'}
        </button>
        <img src="${imgUrl}" alt="${escapeHtml(dish.name)}" class="dish-card-img" loading="lazy" onerror="this.src='${defaultImg}'">
        <span class="dish-card-badge" style="${!isAvailable ? 'color:#f87171; border-color:rgba(239,68,68,0.4);' : ''}">
          ${isAvailable ? `${categoryLabel || 'Còn món'} · ${ratingText}` : 'Hết hàng'}
        </span>
      </div>
      <div class="dish-card-body">
        <h3 class="dish-card-title">${escapeHtml(dish.name)}</h3>
        <p class="dish-card-desc">${escapeHtml(dish.description || 'Món ăn đêm thơm ngon nóng sốt chế biến ngay khi đặt hàng.')}</p>
        <div class="dish-card-footer">
          <div class="dish-price">${formatVND(dish.price)}</div>
          <div class="dish-card-actions" style="display:flex; gap:8px;">
            <a href="product-detail.html?id=${dish.id}" class="btn btn-secondary" style="padding:6px 12px; font-size:0.85rem;">Chi tiết</a>
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
