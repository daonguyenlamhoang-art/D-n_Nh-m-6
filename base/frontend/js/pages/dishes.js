// Logic Thực đơn món ăn: Tìm kiếm & Lọc theo danh mục (FR-01, FR-03, TC-01..04)

let currentCategoryId = "";
let currentSearch = "";
let searchTimeout = null;

document.addEventListener("DOMContentLoaded", async () => {
  await loadCategories();
  await loadDishes();

  const searchInput = document.getElementById("search-input");
  if (searchInput) {
    searchInput.addEventListener("input", (e) => {
      clearTimeout(searchTimeout);
      searchTimeout = setTimeout(() => {
        currentSearch = e.target.value.trim();
        loadDishes();
      }, 300);
    });
  }
});

async function loadCategories() {
  const tabsContainer = document.getElementById("category-tabs-container");
  if (!tabsContainer) return;

  try {
    const categories = await api.get("/categories");
    const tabsHtml = [
      `<button class="category-tab active" data-category-id="">Tất cả món</button>`,
      ...categories.map(c => `
        <button class="category-tab" data-category-id="${c.id}">${escapeHtml(c.name)}</button>
      `)
    ].join("");

    tabsContainer.innerHTML = tabsHtml;

    // Gắn sự kiện click lọc danh mục
    tabsContainer.querySelectorAll(".category-tab").forEach(tab => {
      tab.addEventListener("click", (e) => {
        tabsContainer.querySelectorAll(".category-tab").forEach(t => t.classList.remove("active"));
        e.target.classList.add("active");
        currentCategoryId = e.target.getAttribute("data-category-id");
        loadDishes();
      });
    });

  } catch (err) {
    console.error("Lỗi tải danh mục:", err);
  }
}

async function loadDishes() {
  const grid = document.getElementById("dishes-grid");
  if (!grid) return;

  grid.innerHTML = `
    <div style="grid-column: 1 / -1; text-align:center; padding: 40px; color:var(--text-dim);">
      Đang tìm món ngon đêm nay...
    </div>
  `;

  try {
    const params = {};
    if (currentCategoryId) params.category_id = currentCategoryId;
    if (currentSearch) params.search = currentSearch;

    const dishes = await api.get("/dishes", params);

    if (!dishes || dishes.length === 0) {
      grid.innerHTML = `
        <div style="grid-column: 1 / -1; text-align:center; padding: 60px 20px;">
          <div style="font-size:3rem; margin-bottom:12px;">🔍</div>
          <h3 style="color:var(--text-main); margin-bottom:6px;">Không tìm thấy món ăn nào phù hợp</h3>
          <p style="color:var(--text-muted); font-size:0.9rem;">Thử tìm kiếm với từ khóa khác hoặc chọn danh mục khác bạn nhé!</p>
        </div>
      `;
      return;
    }

    grid.innerHTML = dishes.map(dish => renderDishCard(dish)).join("");

    // Gắn sự kiện thêm món
    grid.querySelectorAll(".btn-add-cart").forEach(btn => {
      btn.addEventListener("click", (e) => {
        const dishId = parseInt(e.target.getAttribute("data-id"));
        CartStorage.addItem(dishId, 1);
      });
    });

  } catch (err) {
    grid.innerHTML = `
      <div style="grid-column: 1 / -1; text-align:center; padding: 40px; color:var(--danger);">
        Không thể tải danh sách món: ${escapeHtml(err.message)}
      </div>
    `;
  }
}

function renderDishCard(dish) {
  const defaultImg = "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=500&auto=format&fit=crop&q=60";
  const imgUrl = dish.image_url ? escapeHtml(dish.image_url) : defaultImg;
  const isAvailable = dish.is_available;
  const categoryLabel = dish.category_name ? escapeHtml(dish.category_name) : "";

  return `
    <div class="dish-card">
      <div class="dish-card-img-wrapper">
        <img src="${imgUrl}" alt="${escapeHtml(dish.name)}" class="dish-card-img" loading="lazy" onerror="this.src='${defaultImg}'">
        <span class="dish-card-badge" style="${!isAvailable ? 'color:#f87171; border-color:rgba(239,68,68,0.4);' : ''}">
          ${isAvailable ? (categoryLabel || 'Còn món') : 'Hết hàng'}
        </span>
      </div>
      <div class="dish-card-body">
        <h3 class="dish-card-title">${escapeHtml(dish.name)}</h3>
        <p class="dish-card-desc">${escapeHtml(dish.description || 'Món ăn đêm thơm ngon nóng sốt chế biến ngay khi đặt hàng.')}</p>
        <div class="dish-card-footer">
          <div class="dish-price">${formatVND(dish.price)}</div>
          <div class="dish-card-actions">
            <a href="product-detail.html?id=${dish.id}" class="btn btn-secondary" style="padding:6px 12px; font-size:0.85rem;">Chi tiết</a>
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
