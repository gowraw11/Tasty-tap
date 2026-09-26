/* ==========================================================================
   TASTY TAP — Interactive Frontend Engine
   Handles: Dynamic Region Transitions, Smart Multi-Vendor Cart, Live Search,
   Food Customization, Smart Meal Builder, TAP AI Assistant, Three.js & GSAP
   ========================================================================== */

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function showToast(message) {
    let container = document.getElementById('tt-toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'tt-toast-container';
        container.className = 'tt-toast-container';
        document.body.appendChild(container);
    }
    const toast = document.createElement('div');
    toast.className = 'tt-toast';
    toast.innerHTML = `<span>✨ ${message}</span>`;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3200);
}

/* 1. Dark Mode Persistence (Section 41) */
function initDarkMode() {
    const saved = localStorage.getItem('tasty_tap_dark_mode');
    if (saved === 'true') {
        document.body.classList.add('dark-mode');
    }
    const toggleBtn = document.getElementById('tt-dark-toggle');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', () => {
            document.body.classList.toggle('dark-mode');
            const isDark = document.body.classList.contains('dark-mode');
            localStorage.setItem('tasty_tap_dark_mode', isDark ? 'true' : 'false');
            toggleBtn.textContent = isDark ? '☀️' : '🌙';
        });
    }
}

/* 2. Dynamic Region Transition Animation (Sections 71, 88, 92) */
async function selectRegionWithTransition(regionSlug, regionName, regionEmoji, currentRegionName) {
    const overlay = document.getElementById('tt-region-transition-overlay');
    const fromEl = document.getElementById('tt-transition-from');
    const toEl = document.getElementById('tt-transition-to');

    const regionModal = document.getElementById('tt-region-modal');
    if (regionModal) regionModal.classList.remove('open');

    if (overlay) {
        if (fromEl) {
            fromEl.textContent = currentRegionName ? `From ${currentRegionName}...` : 'Preparing your regional table...';
        }
        if (toEl) {
            toEl.textContent = `...to ${regionName} ${regionEmoji || '🇮🇳'}`;
        }
        overlay.classList.add('active');
    }

    try {
        await fetch('/api/regions/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ region_slug: regionSlug })
        });
    } catch (e) {
        console.warn('Region switch fallback navigation', e);
    }

    setTimeout(() => {
        const url = new URL(window.location.href);
        url.searchParams.set('region', regionSlug);
        window.location.href = url.toString();
    }, 1150);
}

/* 3. Flying to Cart Animation + Smart Multi-Vendor Cart API (Sections 9, 37, 38) */
let pendingConflictOrder = null;

function triggerFlyingAnimation(sourceElem) {
    if (!sourceElem) return;
    const rect = sourceElem.getBoundingClientRect();
    const target = document.getElementById('tt-quick-cart-box') || document.getElementById('tt-nav-cart-btn');
    if (!target) return;
    const targetRect = target.getBoundingClientRect();

    const flyer = document.createElement('div');
    flyer.textContent = '🍲';
    flyer.style.position = 'fixed';
    flyer.style.left = `${rect.left + rect.width / 2}px`;
    flyer.style.top = `${rect.top}px`;
    flyer.style.fontSize = '1.4rem';
    flyer.style.zIndex = '5000';
    flyer.style.pointerEvents = 'none';
    flyer.style.transition = 'all 0.65s cubic-bezier(0.2, 0.8, 0.2, 1)';
    document.body.appendChild(flyer);

    requestAnimationFrame(() => {
        flyer.style.left = `${targetRect.left + 30}px`;
        flyer.style.top = `${targetRect.top + 20}px`;
        flyer.style.transform = 'scale(0.35)';
        flyer.style.opacity = '0.2';
    });
    setTimeout(() => flyer.remove(), 680);
}

async function addToCart(foodId, quantity = 1, size = 'Regular', spice = 'Medium', addons = '', addonPrice = 0, forceSeparate = false, btnElem = null) {
    try {
        const resp = await fetch('/api/cart/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                action: 'add',
                food_id: foodId,
                quantity: quantity,
                size: size,
                spice: spice,
                addons: addons,
                addon_price: addonPrice,
                force_separate: forceSeparate
            })
        });
        const data = await resp.json();

        if (resp.status === 409 && data.conflict) {
            pendingConflictOrder = { foodId, quantity, size, spice, addons, addonPrice };
            openConflictModal(data.current_business, data.new_business, data.message);
            return;
        }

        if (!resp.ok) {
            showToast(data.error || 'Unable to add item to cart.');
            return;
        }

        triggerFlyingAnimation(btnElem);
        showToast(data.message || 'Added to Quick Order Cart!');
        renderQuickCart(data.cart);
        closeCustomizeModal();
    } catch (err) {
        console.error(err);
        showToast('Could not connect to cart service.');
    }
}

async function updateCartQty(itemId, delta) {
    try {
        const resp = await fetch('/api/cart/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                action: 'update_qty',
                item_id: itemId,
                delta: delta
            })
        });
        const data = await resp.json();
        if (resp.ok && data.cart) {
            renderQuickCart(data.cart);
            if (window.location.pathname.indexOf('/cart/') !== -1) {
                window.location.reload();
            }
        }
    } catch (err) {
        console.error(err);
    }
}

function renderQuickCart(cart) {
    const badgeList = document.querySelectorAll('.js-cart-count');
    badgeList.forEach(el => {
        el.textContent = cart.item_count;
    });

    const container = document.getElementById('tt-quick-cart-items');
    const totalEl = document.getElementById('tt-quick-cart-total');
    const storeEl = document.getElementById('tt-quick-cart-store');
    const delEstEl = document.getElementById('tt-quick-cart-del-est');
    const freeBarEl = document.getElementById('tt-quick-cart-free-bar');

    if (storeEl) {
        storeEl.textContent = cart.business_name ? `Ordering from ${cart.business_name}` : 'Add items from any local business';
    }
    if (totalEl) {
        totalEl.textContent = `₹${Math.round(cart.total)}`;
    }
    if (delEstEl) {
        delEstEl.textContent = `Delivery Estimation: ${cart.business_delivery_time || '20–25m'}`;
    }
    if (freeBarEl && cart.free_delivery_progress) {
        const p = cart.free_delivery_progress;
        const msg = p.unlocked
            ? '🎉 Free Delivery Unlocked!'
            : `Add ₹${Math.round(p.remaining)} more for FREE Delivery`;
        freeBarEl.innerHTML = `
            <div>${msg}</div>
            <div class="tt-progress-track">
                <div class="tt-progress-fill" style="width:${p.percent}%"></div>
            </div>
        `;
    }

    if (!container) return;

    if (!cart.items || cart.items.length === 0) {
        container.innerHTML = `
            <div style="text-align:center; padding:1.4rem 0.5rem; color:var(--text-muted); font-size:0.85rem;">
                🍲 Your Quick Order Cart is empty.<br>Tap <strong>Add +</strong> on any dish to begin!
            </div>
        `;
        return;
    }

    container.innerHTML = cart.items.map(item => `
        <div class="tt-qcart-item">
            <img src="${item.image_url}" alt="${item.name}" class="tt-qcart-thumb">
            <div>
                <div class="tt-qcart-name">${item.name} <span class="tt-star">★ ${item.rating}</span></div>
                <div class="tt-qcart-sub">${item.customization || `${item.prep_time} mins`}</div>
                <div class="tt-qcart-price">₹${Math.round(item.line_total)}</div>
            </div>
            <div class="tt-qty-stepper">
                <button type="button" class="tt-qty-btn" onclick="updateCartQty(${item.id}, -1)">-</button>
                <span style="font-size:0.82rem; font-weight:700; min-width:14px; text-align:center;">${item.quantity}</span>
                <button type="button" class="tt-qty-btn" onclick="updateCartQty(${item.id}, 1)">+</button>
            </div>
        </div>
    `).join('');
}

/* 4. Multi-Vendor Cart Conflict Modal (Section 9) */
function openConflictModal(currentBiz, newBiz, message) {
    const modal = document.getElementById('tt-conflict-modal');
    if (!modal) return;
    const msgEl = document.getElementById('tt-conflict-message');
    if (msgEl) {
        msgEl.innerHTML = `
            Your cart currently has items from <strong>${currentBiz}</strong>.<br>
            You selected a dish from <strong>${newBiz}</strong>.<br><br>
            ${message}
        `;
    }
    modal.classList.add('open');
}

function closeConflictModal() {
    const modal = document.getElementById('tt-conflict-modal');
    if (modal) modal.classList.remove('open');
    pendingConflictOrder = null;
}

function confirmSeparateOrder() {
    if (!pendingConflictOrder) return;
    const o = pendingConflictOrder;
    closeConflictModal();
    addToCart(o.foodId, o.quantity, o.size, o.spice, o.addons, o.addonPrice, true, null);
}

/* 5. Dynamic Food Customization Modal (Section 36) */
let activeCustomizeFood = null;

function openCustomizeModal(foodId, foodName, basePrice) {
    activeCustomizeFood = { id: foodId, name: foodName, basePrice: parseFloat(basePrice) };
    const modal = document.getElementById('tt-customize-modal');
    const titleEl = document.getElementById('tt-cust-title');
    if (titleEl) titleEl.textContent = `Customize ${foodName}`;
    // Reset inputs
    document.querySelectorAll('input[name="cust_size"]').forEach((r, i) => { r.checked = i === 0; });
    document.querySelectorAll('input[name="cust_spice"]').forEach((r, i) => { r.checked = i === 1; });
    document.querySelectorAll('input[name="cust_addon"]').forEach(c => { c.checked = false; });
    recalcCustomizePrice();
    if (modal) modal.classList.add('open');
}

function closeCustomizeModal() {
    const modal = document.getElementById('tt-customize-modal');
    if (modal) modal.classList.remove('open');
}

function recalcCustomizePrice() {
    if (!activeCustomizeFood) return;
    let delta = 0;
    const sizeChecked = document.querySelector('input[name="cust_size"]:checked');
    if (sizeChecked) delta += parseFloat(sizeChecked.dataset.price || '0');
    document.querySelectorAll('input[name="cust_addon"]:checked').forEach(cb => {
        delta += parseFloat(cb.dataset.price || '0');
    });
    const total = activeCustomizeFood.basePrice + delta;
    const priceLabel = document.getElementById('tt-cust-live-price');
    if (priceLabel) priceLabel.textContent = `₹${Math.round(total)}`;
}

function submitCustomizedFood() {
    if (!activeCustomizeFood) return;
    const sizeChecked = document.querySelector('input[name="cust_size"]:checked');
    const spiceChecked = document.querySelector('input[name="cust_spice"]:checked');
    const sizeVal = sizeChecked ? sizeChecked.value : 'Regular';
    const spiceVal = spiceChecked ? spiceChecked.value : 'Medium';

    let delta = sizeChecked ? parseFloat(sizeChecked.dataset.price || '0') : 0;
    const addons = [];
    document.querySelectorAll('input[name="cust_addon"]:checked').forEach(cb => {
        addons.push(cb.value);
        delta += parseFloat(cb.dataset.price || '0');
    });

    addToCart(activeCustomizeFood.id, 1, sizeVal, spiceVal, addons.join(', '), delta, false, null);
}

/* 6. AJAX Live Search with Region Priority & All-India Toggle (Sections 23, 87) */
function initLiveSearch() {
    const input = document.getElementById('tt-live-search-input');
    const dropdown = document.getElementById('tt-live-search-dropdown');
    const allIndiaToggle = document.getElementById('tt-search-all-india');
    if (!input || !dropdown) return;

    let timer = null;
    const performSearch = async () => {
        const q = input.value.trim();
        if (q.length < 2) {
            dropdown.classList.remove('active');
            return;
        }
        const allIndia = allIndiaToggle && allIndiaToggle.checked ? 'true' : 'false';
        try {
            const resp = await fetch(`/api/search/?q=${encodeURIComponent(q)}&all_india=${allIndia}`);
            const data = await resp.json();
            renderSearchResults(data, dropdown);
        } catch (err) {
            console.error(err);
        }
    };

    input.addEventListener('input', () => {
        clearTimeout(timer);
        timer = setTimeout(performSearch, 220);
    });
    if (allIndiaToggle) {
        allIndiaToggle.addEventListener('change', performSearch);
    }
    document.addEventListener('click', (e) => {
        if (!input.contains(e.target) && !dropdown.contains(e.target)) {
            dropdown.classList.remove('active');
        }
    });
}

function renderSearchResults(data, dropdown) {
    const foods = data.foods || [];
    const businesses = data.businesses || [];
    let html = `
        <div style="display:flex; justify-content:space-between; align-items:center; font-size:0.76rem; color:var(--text-muted); margin-bottom:0.5rem;">
            <span>Prioritizing: <strong>${data.prioritized_region}</strong></span>
            <a href="/explore/?q=${encodeURIComponent(data.query)}" style="color:var(--region-primary); font-weight:700;">View All →</a>
        </div>
    `;

    if (businesses.length > 0) {
        html += `<div style="font-size:0.74rem; font-weight:800; text-transform:uppercase; color:var(--text-muted); margin:0.4rem 0;">Local Food Businesses</div>`;
        businesses.slice(0, 3).forEach(b => {
            html += `
                <a href="/store/${b.slug}/" style="display:flex; justify-content:space-between; align-items:center; padding:0.45rem 0.5rem; border-radius:8px; border-bottom:1px solid var(--border-soft);">
                    <div>
                        <div style="font-weight:700; font-size:0.86rem;">${b.marker_emoji} ${b.name}</div>
                        <div style="font-size:0.74rem; color:var(--text-muted);">${b.city} • ${b.cuisine}</div>
                    </div>
                    <span class="tt-star" style="font-size:0.8rem;">★ ${b.rating}</span>
                </a>
            `;
        });
    }

    if (foods.length > 0) {
        html += `<div style="font-size:0.74rem; font-weight:800; text-transform:uppercase; color:var(--text-muted); margin:0.55rem 0 0.35rem;">Matching Dishes</div>`;
        foods.slice(0, 5).forEach(f => {
            html += `
                <div style="display:flex; justify-content:space-between; align-items:center; padding:0.45rem 0.5rem; border-bottom:1px dashed var(--border-soft);">
                    <a href="/food/${f.slug}/" style="flex:1;">
                        <div style="font-weight:700; font-size:0.86rem;">${f.name} — ₹${Math.round(f.effective_price)}</div>
                        <div style="font-size:0.73rem; color:var(--text-muted);">by ${f.business_name} (${f.region_name})</div>
                    </a>
                    <button type="button" class="btn-add-food" style="padding:0.28rem 0.65rem; font-size:0.75rem;" onclick="addToCart(${f.id}, 1)">Add +</button>
                </div>
            `;
        });
    }

    if (foods.length === 0 && businesses.length === 0) {
        html += `<div style="padding:0.8rem; text-align:center; font-size:0.84rem; color:var(--text-muted);">No exact match in this region. Try toggling "Search All India"!</div>`;
    }

    dropdown.innerHTML = html;
    dropdown.classList.add('active');
}

/* 7. Smart Meal Builder Generator (Section 22) */
let currentMealPlanFoodIds = [];

async function generateSmartMeal() {
    const budget = document.getElementById('mb-budget')?.value || 500;
    const people = document.getElementById('mb-people')?.value || 2;
    const cuisine = document.getElementById('mb-cuisine')?.value || '';
    const veg = document.getElementById('mb-veg')?.value || 'ANY';
    const spice = document.getElementById('mb-spice')?.value || 'ANY';
    const container = document.getElementById('mb-results-container');

    try {
        const resp = await fetch('/api/recommendations/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                mode: 'meal_builder',
                budget: budget,
                people: people,
                cuisine: cuisine,
                veg_type: veg,
                spice_level: spice
            })
        });
        const data = await resp.json();
        currentMealPlanFoodIds = (data.courses || []).map(c => ({ food_id: c.food_id, quantity: c.quantity }));

        if (container && data.courses) {
            container.innerHTML = `
                <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:0.75rem; margin-top:1.25rem; padding:0.9rem 1.2rem; background:var(--surface-card); border-radius:14px; border:1px solid var(--border-soft);">
                    <div>
                        <strong>Generated ${data.courses.length}-Course Meal for ${data.people} People</strong>
                        <span style="margin-left:0.75rem; font-size:0.85rem; color:var(--text-muted);">Total Calories: ~${data.total_calories} kcal</span>
                    </div>
                    <div style="display:flex; align-items:center; gap:1rem;">
                        <span style="font-size:1.25rem; font-weight:800; color:var(--region-primary);">Total: ₹${Math.round(data.total_price)}</span>
                        <button type="button" class="btn-coastal-teal" onclick="addSmartMealBundleToCart()">Add Full Meal to Cart 🛒</button>
                    </div>
                </div>
                <div class="tt-meal-courses-grid">
                    ${data.courses.map(c => `
                        <div class="tt-meal-slot-card">
                            <div style="font-size:0.72rem; font-weight:800; text-transform:uppercase; color:var(--region-secondary); margin-bottom:0.35rem;">${c.course_label}</div>
                            <img src="${c.image_url}" alt="${c.name}" style="width:100%; height:110px; object-fit:cover; border-radius:10px; margin-bottom:0.5rem;">
                            <div style="font-weight:700; font-size:0.92rem;">${c.name}</div>
                            <div style="font-size:0.76rem; color:var(--text-muted); margin-bottom:0.4rem;">${c.business_name}</div>
                            <div style="display:flex; justify-content:space-between; align-items:center; font-size:0.84rem; font-weight:700;">
                                <span>Qty: ×${c.quantity}</span>
                                <span>₹${Math.round(c.line_total)}</span>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
            showToast(`Smart Meal generated: ₹${Math.round(data.total_price)} for ${data.people} people!`);
        }
    } catch (err) {
        console.error(err);
    }
}

async function addSmartMealBundleToCart() {
    if (!currentMealPlanFoodIds || currentMealPlanFoodIds.length === 0) {
        const cards = document.querySelectorAll('[data-meal-food-id]');
        currentMealPlanFoodIds = Array.from(cards).map(el => ({
            food_id: parseInt(el.dataset.mealFoodId, 10),
            quantity: parseInt(el.dataset.mealQty || '1', 10)
        }));
    }
    if (currentMealPlanFoodIds.length === 0) return;

    const resp = await fetch('/api/cart/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            action: 'add_bundle',
            food_ids: currentMealPlanFoodIds,
            force_replace: true
        })
    });
    const data = await resp.json();
    if (resp.ok && data.cart) {
        renderQuickCart(data.cart);
        showToast('Added complete Smart Meal to your cart!');
    }
}

/* 8. TAP AI Assistant Chatbot (Sections 21, 86) */
function toggleTapAIDrawer() {
    const drawer = document.getElementById('tt-tap-ai-drawer');
    if (drawer) drawer.classList.toggle('open');
}

async function sendTapAIQuery(promptText) {
    const input = document.getElementById('tt-tap-ai-input');
    const chatLog = document.getElementById('tt-tap-ai-messages');
    const query = promptText || (input ? input.value.trim() : '');
    if (!query || !chatLog) return;
    if (input && !promptText) input.value = '';

    chatLog.innerHTML += `
        <div style="align-self:flex-end; background:var(--region-primary); color:#fff; padding:0.55rem 0.85rem; border-radius:14px 14px 2px 14px; font-size:0.83rem; max-width:85%;">
            ${query}
        </div>
    `;
    chatLog.scrollTop = chatLog.scrollHeight;

    try {
        const resp = await fetch('/api/recommendations/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ mode: 'tap_ai', query: query })
        });
        const data = await resp.json();
        const foodsHtml = (data.foods || []).map(f => `
            <div style="display:flex; justify-content:space-between; align-items:center; background:var(--surface-card); padding:0.45rem 0.6rem; border-radius:10px; margin-top:0.4rem; border:1px solid var(--border-soft);">
                <div>
                    <div style="font-weight:700; font-size:0.8rem;">${f.name} — ₹${Math.round(f.price)}</div>
                    <div style="font-size:0.7rem; color:var(--text-muted);">${f.business_name} • ★ ${f.rating}</div>
                </div>
                <button type="button" class="btn-add-food" style="padding:0.25rem 0.55rem; font-size:0.72rem;" onclick="addToCart(${f.id}, 1)">Add +</button>
            </div>
        `).join('');

        chatLog.innerHTML += `
            <div style="align-self:flex-start; background:var(--region-bg); color:var(--text-main); padding:0.7rem 0.85rem; border-radius:14px 14px 14px 2px; font-size:0.82rem; max-width:92%; border:1px solid var(--border-soft);">
                <div>🤖 <strong>TAP AI (${data.region}):</strong> ${data.reply}</div>
                ${foodsHtml}
            </div>
        `;
        chatLog.scrollTop = chatLog.scrollHeight;
    } catch (err) {
        console.error(err);
    }
}

/* 9. Wishlist Heart Toggle (Section 29) */
async function toggleWishlistItem(type, id, btnElem) {
    try {
        const payload = type === 'food' ? { food_id: id } : { business_id: id };
        const resp = await fetch('/api/wishlist/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(payload)
        });
        if (resp.status === 401) {
            showToast('Please sign in to save items to My Favorites ❤️');
            return;
        }
        const data = await resp.json();
        if (btnElem) {
            btnElem.classList.toggle('saved', data.saved);
            btnElem.textContent = data.saved ? '♥' : '♡';
        }
        showToast(data.saved ? 'Saved to My Favorites ❤️' : 'Removed from Favorites');
    } catch (err) {
        console.error(err);
    }
}

/* 10. "Our Menu" Tab Switcher (Breakfast / Lunch / Dinner / All) */
function switchMenuTab(tabKey, btnElem) {
    document.querySelectorAll('.tt-menu-tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn === btnElem);
    });
    const cards = document.querySelectorAll('.tt-our-menu-item');
    cards.forEach(card => {
        const tabs = (card.dataset.menuTabs || 'ALL').split(',');
        if (tabKey === 'ALL' || tabs.includes(tabKey)) {
            card.style.display = 'grid';
        } else {
            card.style.display = 'none';
        }
    });
}

/* 11. Built-in Tasty Tap Map Tile Engine & Layer Switcher (Zero API-Key Errors / Zero 403s) */
function attachTastyTapMapLayers(mapInstance) {
    if (!mapInstance || typeof L === 'undefined') return null;
    const apiKey = window.TASTY_TAP_MAPS_API_KEY || 'tt_maps_live_9f8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c';

    const tastyTapStreetLayer = L.tileLayer(`/api/map-tiles/{z}/{x}/{y}.png?style=street&key=${apiKey}`, {
        maxZoom: 19,
        attribution: '&copy; Tasty Tap Maps Engine &bull; OpenStreetMap &amp; CARTO'
    });

    const esriStreetLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}', {
        maxZoom: 19,
        attribution: '&copy; Esri World Street Map &bull; Tasty Tap Maps'
    });

    const satelliteLayer = L.tileLayer(`/api/map-tiles/{z}/{x}/{y}.png?style=satellite&key=${apiKey}`, {
        maxZoom: 19,
        attribution: '&copy; Esri World Imagery &bull; Tasty Tap Satellite'
    });

    const lightLayer = L.tileLayer(`/api/map-tiles/{z}/{x}/{y}.png?style=light&key=${apiKey}`, {
        maxZoom: 19,
        attribution: '&copy; CARTO Light &bull; Tasty Tap Maps'
    });

    // Automatic fallback if any external tile fails to load
    [esriStreetLayer].forEach(layer => {
        layer.on('tileerror', (err) => {
            if (err && err.tile && err.coords && !err.tile.dataset.ttFallbackApplied) {
                err.tile.dataset.ttFallbackApplied = '1';
                err.tile.src = `/api/map-tiles/${err.coords.z}/${err.coords.x}/${err.coords.y}.png?style=street&key=${apiKey}`;
            }
        });
    });

    tastyTapStreetLayer.addTo(mapInstance);

    const baseLayers = {
        '🗺️ Tasty Tap Street HD': tastyTapStreetLayer,
        '🧭 Esri World Street Map': esriStreetLayer,
        '🛰️ Satellite View': satelliteLayer,
        '✨ Clean Light Map': lightLayer
    };
    L.control.layers(baseLayers, null, { position: 'topright', collapsed: true }).addTo(mapInstance);

    return tastyTapStreetLayer;
}

document.addEventListener('DOMContentLoaded', () => {
    initDarkMode();
    initLiveSearch();
});

