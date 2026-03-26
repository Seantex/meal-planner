/* ═══════════════════════════════════════════════════════════════
   Meal Planner – JavaScript v20 (Nova)
   ═══════════════════════════════════════════════════════════════ */

// ── Scroll Reveal ───────────────────────────────────────────────────────────
document.documentElement.classList.add('js-ready');

// ── Cursor Spotlight ────────────────────────────────────────────────────────
(function initCursorSpotlight() {
  const el = document.getElementById('cursor-spotlight');
  if (!el) return;
  let raf;
  let tx = window.innerWidth / 2, ty = window.innerHeight / 2;
  let cx = tx, cy = ty;

  document.addEventListener('mousemove', e => {
    tx = e.clientX; ty = e.clientY;
    if (!raf) raf = requestAnimationFrame(loop);
  });

  function loop() {
    cx += (tx - cx) * 0.12;
    cy += (ty - cy) * 0.12;
    el.style.setProperty('--cx', cx + 'px');
    el.style.setProperty('--cy', cy + 'px');
    const dist = Math.hypot(tx - cx, ty - cy);
    raf = dist > 0.5 ? requestAnimationFrame(loop) : null;
  }
})();

// ── Navbar scroll state ─────────────────────────────────────────────────────
(function initNavbarScroll() {
  const nav = document.querySelector('.navbar');
  if (!nav) return;
  const update = () => nav.classList.toggle('scrolled', window.scrollY > 20);
  window.addEventListener('scroll', update, { passive: true });
  update();
})();

// ── Button Ripple Effect ────────────────────────────────────────────────────
document.addEventListener('pointerdown', function(e) {
  const btn = e.target.closest('.btn');
  if (!btn) return;
  const rect = btn.getBoundingClientRect();
  const size = Math.max(rect.width, rect.height) * 2;
  const ripple = document.createElement('span');
  ripple.className = 'ripple';
  ripple.style.cssText = `
    width:${size}px; height:${size}px;
    left:${e.clientX - rect.left - size/2}px;
    top:${e.clientY - rect.top - size/2}px;
  `;
  btn.appendChild(ripple);
  setTimeout(() => ripple.remove(), 600);
}, { passive: true });

// ── Checkbox Particle Burst ─────────────────────────────────────────────────
document.addEventListener('change', function(e) {
  if (!e.target.classList.contains('item-checkbox') || !e.target.checked) return;
  const wrap = e.target.parentElement;
  if (!wrap) return;
  const colors = ['#9b5cf6','#f472b6','#22d3ee','#34d399','#a78bfa'];
  for (let i = 0; i < 8; i++) {
    const p = document.createElement('span');
    p.className = 'check-burst';
    const angle = (i / 8) * Math.PI * 2;
    const dist = 18 + Math.random() * 14;
    const dx = Math.cos(angle) * dist;
    const dy = Math.sin(angle) * dist;
    p.style.cssText = `
      left:50%; top:50%;
      background:${colors[i % colors.length]};
      --tx:translate(${dx}px,${dy}px);
      width:${4 + Math.random()*3}px;
      height:${4 + Math.random()*3}px;
      margin:-3px;
    `;
    wrap.appendChild(p);
    setTimeout(() => p.remove(), 550);
  }
}, { passive: true });

// ── Number Countup ──────────────────────────────────────────────────────────
(function initCountup() {
  function animate(el) {
    const target = parseFloat(el.textContent.replace(/[^0-9.]/g,'')) || 0;
    if (target === 0 || target > 9999) return;
    const duration = 900;
    const start = performance.now();
    const prefix = el.textContent.match(/^[^0-9]*/)?.[0] || '';
    const suffix = el.textContent.match(/[^0-9.]*$/)?.[0] || '';
    function step(now) {
      const t = Math.min((now - start) / duration, 1);
      const ease = 1 - Math.pow(1 - t, 3);
      const val = Math.round(target * ease);
      el.textContent = prefix + val + suffix;
      if (t < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }

  const obs = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        animate(e.target);
        obs.unobserve(e.target);
      }
    });
  }, { threshold: 0.5 });

  function observe() {
    document.querySelectorAll('.stat-num, .deals-count, .admin-stat').forEach(el => obs.observe(el));
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', observe);
  else observe();
})();

(function initScrollReveal() {
  const obs = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.classList.add('visible');
        obs.unobserve(e.target);
      }
    });
  }, { threshold: 0.06, rootMargin: '0px 0px -30px 0px' });

  function observe() {
    document.querySelectorAll('.reveal').forEach(el => obs.observe(el));
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', observe);
  } else {
    observe();
  }
})();

'use strict';

// ── Page Loader ────────────────────────────────────────────────────────────────

function showPageLoader(text) {
  const el = document.getElementById('page-loader');
  const txt = document.getElementById('page-loader-text');
  if (!el) return;
  if (txt && text) txt.textContent = text;
  el.classList.add('visible');
  el.getBoundingClientRect(); // force repaint before navigation
}

function hidePageLoader() {
  const el = document.getElementById('page-loader');
  if (el) el.classList.remove('visible');
}

// Show loader on all POST form submissions (prevent → paint → submit for reliable animation)
document.addEventListener('submit', function(e) {
  const form = e.target;
  if (form.dataset.submitting || form.dataset.noIntercept) return;
  if (!form.method || form.method.toLowerCase() !== 'post') return;
  e.preventDefault();
  const btn = form.querySelector('button[type="submit"]');
  const label = btn ? btn.textContent.trim() : '';
  if (label.includes('Einkaufsliste')) showPageLoader('Einkaufsliste wird erstellt…');
  else if (label.includes('generieren') || label.includes('Wochenplan')) showPageLoader('Wochenplan wird erstellt…');
  else showPageLoader('Wird verarbeitet…');
  form.dataset.submitting = '1';
  requestAnimationFrame(() => requestAnimationFrame(() => form.submit()));
}, true);

// Show loader on slow navigation links (overview, shopping)
document.addEventListener('click', function(e) {
  const a = e.target.closest('a[href]');
  if (!a) return;
  const href = a.getAttribute('href') || '';
  if (href.includes('/overview') || href.includes('/shopping/') || href.includes('/plan/new')) {
    showPageLoader('Wird geladen…');
  }
}, true);

// Hide loader on normal page load, back/forward cache, and as safety timeout
document.addEventListener('DOMContentLoaded', function() {
  hidePageLoader();
  // Re-evaluate plan footer state in case all meals are already selected
  if (document.querySelector('.plan-footer') && typeof PLAN_ID !== 'undefined') {
    updateProgress();
  }
});
window.addEventListener('pageshow', hidePageLoader);
window.addEventListener('load', hidePageLoader);
// Safety net: force-hide after 60s in case something went wrong
setTimeout(hidePageLoader, 60000);

// ── Loading-State für Formulare (legacy, button-only) ─────────────────────────

function setLoading(form, loadingText) {
  const btn = form.querySelector('button[type="submit"]');
  if (btn) {
    btn.disabled = true;
    btn.dataset.originalText = btn.textContent;
    btn.textContent = loadingText || '⏳ Bitte warten…';
  }
  setTimeout(() => {
    if (btn && btn.disabled) {
      btn.disabled = false;
      btn.textContent = btn.dataset.originalText || btn.textContent;
    }
  }, 60000);
}

// ── Hilfsfunktionen ────────────────────────────────────────────────────────────

async function apiPost(url, data = {}) {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  const json = await res.json().catch(() => ({}));
  if (!res.ok && !json.error) json.error = `Serverfehler (${res.status})`;
  return json;
}

function showToast(msg, type = 'success') {
  const container = document.querySelector('.flash-container')
    || (() => {
      const el = document.createElement('div');
      el.className = 'flash-container';
      document.body.appendChild(el);
      return el;
    })();
  const flash = document.createElement('div');
  flash.className = `flash flash--${type}`;
  flash.innerHTML = `<span>${msg}</span>
    <button class="flash-close" onclick="this.parentElement.remove()">✕</button>`;
  container.appendChild(flash);
  setTimeout(() => flash.remove(), 4000);
}

// ── Planning: Rezept auswählen ─────────────────────────────────────────────────

async function selectRecipe(planId, slotId, recipeId, btn) {
  btn.disabled = true;
  btn.textContent = '…';

  const data = await apiPost(`/plan/${planId}/select`, {
    meal_slot: slotId,
    recipe_id: recipeId,
  });

  if (data.success) {
    const card = document.getElementById(`slot-${slotId}`);
    if (card) {
      card.classList.add('meal-card--done');

      // Status aktualisieren
      const statusEl = card.querySelector('.meal-status');
      if (statusEl) {
        statusEl.textContent = '✓ Gewählt';
        statusEl.className = 'meal-status meal-status--done';
      }

      // Ausgewähltes Rezept anzeigen
      let selDiv = card.querySelector('.selected-recipe');
      if (!selDiv) {
        selDiv = document.createElement('div');
        selDiv.className = 'selected-recipe';
        card.querySelector('.meal-card-header').after(selDiv);
      }
      selDiv.innerHTML = `
        <div class="selected-recipe-info">
          <span class="selected-name">${data.recipe_name}</span>
        </div>
        <button class="btn btn--outline btn--sm change-btn"
                onclick="toggleSuggestions('${slotId}')">Ändern</button>
      `;

      // Vorschläge ausblenden
      const suggestionsWrap = document.getElementById(`suggestions-${slotId}`);
      if (suggestionsWrap) suggestionsWrap.classList.add('suggestions-wrap--hidden');
    }

    // Fortschrittsbalken aktualisieren
    updateProgress();
    showToast(`✓ ${data.recipe_name} ausgewählt`);
  } else {
    showToast('Fehler beim Auswählen', 'error');
    btn.disabled = false;
    btn.textContent = 'Auswählen ✓';
  }
}

function toggleSuggestions(slotId) {
  const wrap = document.getElementById(`suggestions-${slotId}`);
  if (wrap) wrap.classList.toggle('suggestions-wrap--hidden');
}

async function wishRecipe(slotId, planId) {
  const input = document.getElementById(`wish-${slotId}`);
  const resultBox = document.getElementById(`wish-result-${slotId}`);
  const btn = document.querySelector(`#slot-${slotId} .wish-btn`);
  const wish = input?.value?.trim();
  if (!wish) { input?.focus(); return; }

  if (btn) { btn.disabled = true; btn.textContent = '⏳ KI kocht…'; }
  if (resultBox) resultBox.innerHTML = '<div class="loading-spinner">KI erstellt dein Wunsch-Rezept…</div>';

  try {
    const data = await apiPost(`/plan/${planId}/wish/${slotId}`, { wish });
    if (data.success && data.recipe) {
      const r = data.recipe;
      const ings = (r.ingredients || []).filter(i => !i.is_basic);
      resultBox.innerHTML = `
        <div class="wish-recipe-card">
          <div class="wish-recipe-header">
            <span class="wish-recipe-name">${r.name}</span>
            <span class="badge badge--weekend">✨ KI-Rezept</span>
          </div>
          <p class="suggestion-desc">${r.description || ''}</p>
          <div class="suggestion-meta">
            <span class="meta-item">⏱ <strong>${r.prep_time}min</strong> aktiv</span>
            <span class="meta-item">⏰ <strong>${r.total_time}min</strong> gesamt</span>
            <span class="meta-item">🔥 <strong>${r.nutrition_per_portion?.calories || '?'}</strong> kcal</span>
            <span class="meta-item">💪 <strong>${r.nutrition_per_portion?.protein || '?'}g</strong> Protein</span>
            <span class="meta-item meta-item--cost">💰 <strong>ca. €${data.estimated_cost}</strong></span>
          </div>
          ${ings.length ? `
          <details class="suggestion-ingredients" style="margin-top:10px">
            <summary class="suggestion-ingredients-toggle">🧾 Zutaten (${ings.length})</summary>
            <ul class="suggestion-ing-list">
              ${ings.map(i => `<li class="suggestion-ing-item">
                <span class="suggestion-ing-amount">${i.amount ? i.amount + ' ' + (i.unit||'') : ''}</span>
                <span class="suggestion-ing-name">${i.name}</span>
              </li>`).join('')}
            </ul>
          </details>` : ''}
          <div class="wish-recipe-actions">
            <button class="btn btn--primary btn--sm"
                    onclick="selectWishRecipe(${planId}, '${slotId}', ${JSON.stringify(r).replace(/"/g,'&quot;')}, this)">
              Auswählen ✓
            </button>
            <button class="btn btn--ghost btn--sm" onclick="this.closest('.wish-recipe-card').remove(); document.getElementById('wish-${slotId}').value='';">
              Verwerfen
            </button>
          </div>
        </div>`;
    } else {
      resultBox.innerHTML = `<p class="empty-hint">${data.error || 'KI konnte kein Rezept erstellen.'}</p>`;
    }
  } catch(e) {
    resultBox.innerHTML = '<p class="empty-hint">Fehler beim Generieren.</p>';
  }
  if (btn) { btn.disabled = false; btn.textContent = '✨ KI-Rezept'; }
}

async function selectWishRecipe(planId, slotId, recipe, btn) {
  // KI-Rezept temporär in der Session speichern und als Auswahl setzen
  if (btn) { btn.disabled = true; btn.textContent = '⏳…'; }
  try {
    const data = await apiPost(`/plan/${planId}/select`, {
      meal_slot: slotId,
      recipe_id: recipe.id,
      wish_recipe: recipe,
    });
    if (data.success) {
      const card = document.getElementById(`slot-${slotId}`);
      if (card) {
        card.classList.add('meal-card--done');
        const wrap = document.getElementById(`suggestions-${slotId}`);
        if (wrap) wrap.classList.add('suggestions-wrap--hidden');
        // Zeige ausgewähltes Rezept
        const existing = card.querySelector('.selected-recipe');
        if (!existing) {
          const selDiv = document.createElement('div');
          selDiv.className = 'selected-recipe';
          selDiv.innerHTML = `
            <div class="selected-recipe-info">
              <span class="selected-name">${recipe.name}</span>
              <div class="selected-meta">
                <span class="meta-tag">⏱ ${recipe.prep_time}min aktiv</span>
                <span class="meta-tag">✨ KI-Rezept</span>
              </div>
            </div>
            <button class="btn btn--outline btn--sm change-btn" onclick="toggleSuggestions('${slotId}')">Ändern</button>`;
          card.querySelector('.meal-card-header').after(selDiv);
        }
      }
      updateProgress();
    }
  } catch(e) {}
  if (btn) { btn.disabled = false; }
}

async function skipSlot(slotId, planId) {
  const card = document.getElementById(`slot-${slotId}`);
  await apiPost(`/plan/${planId}/skip/${slotId}`);
  // Reload page to reflect skipped state cleanly
  location.reload();
}

async function unskipSlot(slotId, planId) {
  await apiPost(`/plan/${planId}/unskip/${slotId}`);
  location.reload();
}

function updateProgress() {
  const done = document.querySelectorAll('.meal-card--done, .meal-card--skipped').length;
  const total = document.querySelectorAll('.meal-card').length;
  if (total === 0) return;
  const pct = Math.round((done / total) * 100);

  const fill = document.querySelector('.progress-fill');
  if (fill) fill.style.width = pct + '%';

  const label = document.querySelector('.progress-label');
  if (label) label.textContent = `${done}/${total} Gerichte gewählt`;

  // Footer am unten aktualisieren
  const footer = document.querySelector('.plan-footer');
  if (footer && typeof PLAN_ID !== 'undefined') {
    if (done === total) {
      footer.classList.add('plan-footer--ready');
      if (!footer.querySelector('.finish-form')) {
        footer.innerHTML = `
          <div class="finish-alert-inline"><strong>🎉 Alle Gerichte ausgewählt!</strong></div>
          <form class="finish-form" action="/plan/${PLAN_ID}/finish" method="POST" style="display:inline">
            <button class="btn btn--big btn--primary" type="submit">🛒 Einkaufsliste erstellen →</button>
          </form>`;
      }
    } else {
      footer.classList.remove('plan-footer--ready');
      const hint = footer.querySelector('.plan-footer-hint');
      if (hint) hint.textContent = `Noch ${total - done} Gericht(e) ausstehend`;
    }
  }
  // Alten Top-Alert entfernen falls vorhanden
  document.querySelector('.finish-alert')?.remove();
}

// ── Planning: Neue Vorschläge für einen Slot ───────────────────────────────────

async function regenerateSlot(slotId, planId) {
  const btn = document.querySelector(`#slot-${slotId} .regenerate-btn`);
  if (btn) { btn.disabled = true; btn.textContent = '⏳ Lädt…'; }

  const list = document.getElementById(`suggestions-list-${slotId}`);
  if (list) list.innerHTML = '<div class="loading-spinner">Neue Vorschläge werden geladen…</div>';

  const slotCraving = document.getElementById(`craving-${slotId}`)?.value?.trim() || '';
  const globalCraving = document.getElementById('cravings-input')?.value?.trim() || '';
  const cravings = slotCraving || globalCraving;
  const data = await apiPost(`/plan/${planId}/regenerate/${slotId}`, { cravings });

  if (data.success && data.suggestions) {
    if (list) {
      list.innerHTML = data.suggestions.map(s => `
        <div class="suggestion-item" data-recipe-id="${s.recipe_id}">
          <div class="suggestion-main">
            <div class="suggestion-header">
              <span class="suggestion-name">${s.name}</span>
              <div class="suggestion-badges">
                ${s.deal_matches.length ? '<span class="badge badge--deal">🏷️ Angebot</span>' : ''}
                <span class="badge badge--diff-${s.difficulty}">${s.difficulty}</span>
              </div>
            </div>
            <div class="suggestion-meta">
              <span class="meta-item">⏱ <strong>${s.prep_time}min</strong> aktiv</span>
              <span class="meta-item">⏰ <strong>${s.total_time}min</strong> gesamt</span>
              <span class="meta-item">🔥 <strong>${s.nutrition?.calories || '?'}</strong> kcal</span>
              <span class="meta-item">💪 <strong>${s.nutrition?.protein || '?'}g</strong> Protein</span>
              <span class="meta-item meta-item--cost">💰 <strong>ca. €${s.estimated_cost || '?'}</strong></span>
            </div>
            ${s.reason ? `<p class="suggestion-reason">💡 ${s.reason}</p>` : ''}
            ${s.deal_matches.length
              ? `<div class="deal-matches">${s.deal_matches.map(dm =>
                  `<span class="deal-match-chip">${dm}</span>`).join('')}</div>`
              : ''}
            ${s.ingredients && s.ingredients.length ? `
            <details class="suggestion-ingredients">
              <summary class="suggestion-ingredients-toggle">🧾 Zutaten anzeigen (${s.ingredients.length})</summary>
              <ul class="suggestion-ing-list">
                ${s.ingredients.map(ing => {
                  const amt = ing.amount ? (Number.isInteger(ing.amount) ? ing.amount : ing.amount) + ' ' + (ing.unit || '') : '';
                  const cost = s.ing_costs && s.ing_costs[ing.name] > 0
                    ? `<span class="ing-cost-tag">~€${s.ing_costs[ing.name].toFixed(2)}</span>` : '';
                  return `<li class="suggestion-ing-item">
                    <span class="suggestion-ing-amount">${amt}</span>
                    <span class="suggestion-ing-name">${ing.name}</span>
                    ${cost}
                  </li>`;
                }).join('')}
              </ul>
            </details>` : ''}
          </div>
          <div class="suggestion-actions">
            <button class="btn btn--primary btn--sm select-btn"
                    onclick="selectRecipe(${planId}, '${slotId}', '${s.recipe_id}', this)">
              Auswählen ✓
            </button>
            <a href="/recipes/${s.recipe_id}" class="btn btn--ghost btn--sm" target="_blank">
              Rezept ansehen
            </a>
            <div class="recipe-actions-mini">
              <button class="btn-icon" onclick="toggleFavorite('${s.recipe_id}', this)">⭐</button>
              <button class="btn-icon btn-icon--danger"
                      onclick="markNeverAgain('${s.recipe_id}', '${s.name}', this)">🚫</button>
            </div>
          </div>
        </div>
      `).join('');
    }
  } else {
    if (list) list.innerHTML = '<p class="empty-hint">Konnte keine neuen Vorschläge laden.</p>';
  }

  if (btn) { btn.disabled = false; btn.textContent = '🔄 Zufall'; }
}

// ── Favoriten ──────────────────────────────────────────────────────────────────

async function toggleFavorite(recipeId, btn) {
  const isActive = btn.classList.contains('btn-icon--active')
                || btn.classList.contains('btn--active');
  const action = isActive ? 'remove' : 'add';

  const data = await apiPost(`/recipes/favorite/${recipeId}`, { action });
  if (data.success) {
    if (action === 'add') {
      btn.classList.add('btn-icon--active', 'btn--active');
      if (btn.tagName === 'BUTTON' && btn.classList.contains('btn')) {
        btn.textContent = '⭐ Favorit';
      }
      showToast('⭐ Zu Favoriten hinzugefügt');
    } else {
      btn.classList.remove('btn-icon--active', 'btn--active');
      if (btn.tagName === 'BUTTON' && btn.classList.contains('btn')) {
        btn.textContent = '☆ Zu Favoriten';
      }
      showToast('Aus Favoriten entfernt');
    }
  }
}

// ── Nie-Wieder ─────────────────────────────────────────────────────────────────

let _neverRecipeId = null;
let _neverBtn = null;

function markNeverAgain(recipeId, recipeName, btn) {
  _neverRecipeId = recipeId;
  _neverBtn = btn;
  const modal = document.getElementById('never-modal');
  if (modal) {
    modal.classList.remove('hidden');
    const input = document.getElementById('never-reason');
    if (input) input.value = '';
    input?.focus();
  }
}

async function confirmNeverAgain() {
  if (!_neverRecipeId) return;
  const reason = document.getElementById('never-reason')?.value || '';
  const data = await apiPost(`/recipes/never/${_neverRecipeId}`, {
    action: 'add', reason
  });
  if (data.success) {
    // Karte ausblenden
    const card = document.querySelector(`[data-recipe-id="${_neverRecipeId}"]`);
    if (card) {
      if (card.classList.contains('suggestion-item')) {
        card.classList.add('suggestion-item--never');
      } else {
        card.classList.add('recipe-card--never');
      }
    }
    if (_neverBtn) {
      _neverBtn.classList.add('btn-icon--danger-active');
    }
    showToast('🚫 Rezept wird nicht mehr vorgeschlagen', 'warning');
  }
  closeNeverModal();
}

function closeNeverModal() {
  const modal = document.getElementById('never-modal');
  if (modal) modal.classList.add('hidden');
  _neverRecipeId = null;
  _neverBtn = null;
}

async function toggleNever(recipeId, action, btn) {
  const data = await apiPost(`/recipes/never/${recipeId}`, { action });
  if (data.success) {
    const card = btn.closest('.recipe-card');
    if (card) {
      card.classList.remove('recipe-card--never');
      const overlay = card.querySelector('.never-overlay');
      if (overlay) overlay.remove();
    }
    showToast('Rezept wiederhergestellt');
  }
}

// ── Einkaufsliste ──────────────────────────────────────────────────────────────

async function toggleItem(itemId, checkbox) {
  const item = document.getElementById(`item-${itemId}`);
  const data = await apiPost(`/shopping/toggle/${itemId}`);
  if (data.success && item) {
    item.classList.toggle('item--checked', checkbox.checked);
    updateRemainingCount();
  }
}

function updateRemainingCount() {
  const total = document.querySelectorAll('.item-checkbox').length;
  const checked = document.querySelectorAll('.item-checkbox:checked').length;
  const el = document.getElementById('remaining-count');
  if (el) el.textContent = total - checked;
}

// Note Editor
let _noteItemId = null;

function showNoteEditor(itemId, currentNote) {
  _noteItemId = itemId;
  const popup = document.getElementById('note-editor');
  const input = document.getElementById('note-input');
  if (popup) popup.classList.remove('hidden');
  if (input) { input.value = currentNote || ''; input.focus(); }
}

async function saveNote() {
  if (!_noteItemId) return;
  const note = document.getElementById('note-input')?.value || '';
  const data = await apiPost(`/shopping/note/${_noteItemId}`, { note });
  if (data.success) {
    const display = document.getElementById(`note-display-${_noteItemId}`);
    const item = document.getElementById(`item-${_noteItemId}`);
    if (note) {
      if (display) {
        display.textContent = `📝 ${note}`;
      } else if (item) {
        const content = item.querySelector('.item-content');
        const d = document.createElement('div');
        d.className = 'item-note-display';
        d.id = `note-display-${_noteItemId}`;
        d.textContent = `📝 ${note}`;
        content?.appendChild(d);
      }
    } else if (display) {
      display.remove();
    }
    showToast('📝 Notiz gespeichert');
  }
  closeNoteEditor();
}

function closeNoteEditor() {
  const popup = document.getElementById('note-editor');
  if (popup) popup.classList.add('hidden');
  _noteItemId = null;
}

async function deleteItem(itemId) {
  const item = document.getElementById(`item-${itemId}`);
  const itemCost = item ? parseFloat(item.dataset.cost || '0') : 0;
  const data = await apiPost(`/shopping/delete/${itemId}`);
  if (data.success && item) {
    // Subtract item cost from displayed total
    const costEl = document.getElementById('estimated-cost');
    if (costEl && itemCost > 0) {
      const current = parseFloat(costEl.textContent.replace(/[^0-9.]/g, '')) || 0;
      const updated = Math.max(0, current - itemCost);
      costEl.textContent = `~€${Math.round(updated)}`;
    }
    item.style.transition = 'opacity .2s ease, max-height .3s ease';
    item.style.opacity = '0';
    item.style.maxHeight = '0';
    item.style.overflow = 'hidden';
    setTimeout(() => { item.remove(); updateRemainingCount(); }, 300);
    showToast('🗑️ Eintrag entfernt');
  }
}

function checkAllDeals() {
  document.querySelectorAll('.item--deal .item-checkbox').forEach(cb => {
    if (!cb.checked) { cb.checked = true; cb.dispatchEvent(new Event('change')); }
  });
}

function uncheckAll() {
  document.querySelectorAll('.item-checkbox:checked').forEach(cb => {
    cb.checked = false; cb.dispatchEvent(new Event('change'));
  });
}

function printList() { window.print(); }

// ── Keyboard Shortcuts ─────────────────────────────────────────────────────────

document.addEventListener('keydown', e => {
  if (e.key === 'Escape') {
    closeNeverModal();
    closeNoteEditor();
    closeSlotModal();
  }
  if (e.key === 'Enter' && document.activeElement?.closest('#slot-modal')) {
    confirmSlotModal();
  }
  // Enter in note input → speichern
  if (e.key === 'Enter' && document.activeElement?.id === 'note-input') {
    saveNote();
  }
});

// Klick außerhalb Modal schließt es
document.addEventListener('click', e => {
  const neverModal = document.getElementById('never-modal');
  if (neverModal && !neverModal.classList.contains('hidden')) {
    if (e.target === neverModal) closeNeverModal();
  }
  const noteEditor = document.getElementById('note-editor');
  if (noteEditor && !noteEditor.classList.contains('hidden')) {
    if (e.target === noteEditor) closeNoteEditor();
  }
  const slotModal = document.getElementById('slot-modal');
  if (slotModal && !slotModal.classList.contains('hidden')) {
    if (e.target === slotModal) closeSlotModal();
  }
});

// Flash messages auto-dismiss
setTimeout(() => {
  document.querySelectorAll('.flash').forEach(f => {
    f.style.transition = 'opacity .4s ease';
    f.style.opacity = '0';
    setTimeout(() => f.remove(), 400);
  });
}, 5000);

// ── Tage-Grid beim Erstellen eines neuen Plans ────────────────────────────────

const DAY_NAMES = ['Montag','Dienstag','Mittwoch','Donnerstag','Freitag','Samstag','Sonntag'];

let _dayGridOffset = 0;   // how many days shown so far
let _dayGridStart  = null; // start Date

function _localDateKey(d) {
  // Use local date parts to avoid UTC offset shifting the date (e.g. CET = UTC+1)
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

function _addDayRow(grid, d, checked) {
  const key     = _localDateKey(d);
  const dayName = DAY_NAMES[d.getDay() === 0 ? 6 : d.getDay() - 1];
  const isWeekend    = d.getDay() === 0 || d.getDay() === 6;
  const defaultMittag = isWeekend && checked;
  const defaultAbend  = checked;

  const row = document.createElement('div');
  row.className = 'day-row';
  row.id = `day-row-${key}`;
  row.innerHTML = `
    <label class="day-row-check">
      <input type="checkbox" name="day_${key}" value="1"
             ${checked ? 'checked' : ''}
             onchange="toggleDayRow('${key}', this.checked)">
      <span class="day-row-name">${dayName}</span>
      <span class="day-row-date">${d.toLocaleDateString('de-AT',{day:'numeric',month:'short'})}</span>
    </label>
    <div class="day-row-meals" id="meals-${key}" style="${checked ? '' : 'opacity:.35'}">
      <label class="meal-check">
        <input type="checkbox" name="meal_${key}" value="mittag"
               ${defaultMittag ? 'checked' : ''} ${checked ? '' : 'disabled'}>
        Mittag
      </label>
      <label class="meal-check">
        <input type="checkbox" name="meal_${key}" value="abend"
               ${defaultAbend ? 'checked' : ''} ${checked ? '' : 'disabled'}>
        Abend
      </label>
    </div>
    <button type="button" class="day-row-del" title="Tag entfernen"
            onclick="removeDayRow('${key}')">✕</button>`;
  // Insert before the +button row if it exists
  const addBtn = document.getElementById('day-grid-add-btn');
  if (addBtn) grid.insertBefore(row, addBtn);
  else grid.appendChild(row);
}

function buildDayGrid() {
  const grid = document.getElementById('day-grid');
  const dateInput = document.getElementById('plan-start-date');
  if (!grid || !dateInput?.value) return;

  _dayGridStart = new Date(dateInput.value + 'T00:00:00');
  _dayGridOffset = 0;
  grid.innerHTML = '';

  // First 7 days
  for (let i = 0; i < 7; i++) {
    const d = new Date(_dayGridStart);
    d.setDate(d.getDate() + i);
    _addDayRow(grid, d, true);
    _dayGridOffset++;
  }

  // "+ Weiteren Tag" button
  const addBtn = document.createElement('button');
  addBtn.type = 'button';
  addBtn.id = 'day-grid-add-btn';
  addBtn.className = 'btn btn--outline btn--sm';
  addBtn.style.marginTop = '6px';
  addBtn.textContent = '＋ Weiteren Tag hinzufügen';
  addBtn.onclick = addNextDay;
  grid.appendChild(addBtn);
}

function addNextDay() {
  if (!_dayGridStart || _dayGridOffset >= 14) return;
  const grid = document.getElementById('day-grid');
  const d = new Date(_dayGridStart);
  d.setDate(d.getDate() + _dayGridOffset);
  _addDayRow(grid, d, false);
  _dayGridOffset++;
  if (_dayGridOffset >= 14) {
    const addBtn = document.getElementById('day-grid-add-btn');
    if (addBtn) addBtn.style.display = 'none';
  }
}

function removeDayRow(key) {
  const row = document.getElementById(`day-row-${key}`);
  if (row) row.remove();
}

function toggleDayRow(key, checked) {
  const mealsDiv = document.getElementById(`meals-${key}`);
  if (mealsDiv) {
    mealsDiv.style.opacity = checked ? '1' : '.35';
    mealsDiv.querySelectorAll('input[type=checkbox]').forEach(cb => cb.disabled = !checked);
  }
}

// Grid beim Laden der Seite initialisieren
document.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('day-grid')) buildDayGrid();
});

// ── Slot Management (hinzufügen / bearbeiten / löschen) ───────────────────────

let _slotModalMode = 'add'; // 'add' | 'edit'
let _slotEditId = null;
let _slotEditPlanId = null;

function openAddSlot() {
  _slotModalMode = 'add';
  _slotEditId = null;
  _slotEditPlanId = typeof PLAN_ID !== 'undefined' ? PLAN_ID : null;
  const modal = document.getElementById('slot-modal');
  document.getElementById('slot-modal-title').textContent = 'Mahlzeit hinzufügen';
  document.getElementById('slot-modal-label').value = '';
  document.getElementById('slot-modal-note').value = '';
  document.getElementById('slot-modal-leftovers').checked = false;
  modal?.classList.remove('hidden');
  document.getElementById('slot-modal-label')?.focus();
}

function editSlot(slotId, planId, currentLabel, currentNote, currentLeftovers) {
  _slotModalMode = 'edit';
  _slotEditId = slotId;
  _slotEditPlanId = planId;
  document.getElementById('slot-modal-title').textContent = 'Mahlzeit umbenennen';
  document.getElementById('slot-modal-label').value = currentLabel;
  document.getElementById('slot-modal-note').value = currentNote || '';
  document.getElementById('slot-modal-leftovers').checked = !!currentLeftovers;
  document.getElementById('slot-modal')?.classList.remove('hidden');
  document.getElementById('slot-modal-label')?.focus();
}

async function confirmSlotModal() {
  const label = document.getElementById('slot-modal-label')?.value?.trim();
  const note  = document.getElementById('slot-modal-note')?.value?.trim() || '';
  const leftovers = document.getElementById('slot-modal-leftovers')?.checked || false;
  if (!label) {
    document.getElementById('slot-modal-label')?.focus();
    return;
  }
  const planId = _slotEditPlanId || (typeof PLAN_ID !== 'undefined' ? PLAN_ID : null);
  if (!planId) return;

  if (_slotModalMode === 'add') {
    const data = await apiPost(`/plan/${planId}/slots`, { label, note, leftovers });
    if (data.success) {
      closeSlotModal();
      showPageLoader('Tag wird hinzugefügt…');
      requestAnimationFrame(() => requestAnimationFrame(() => location.reload()));
    } else {
      showToast(data.error || 'Fehler', 'error');
    }
  } else {
    const res = await fetch(`/plan/${planId}/slots/${_slotEditId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ label, note, leftovers }),
    });
    const data = await res.json();
    if (data.success) {
      // Label im DOM direkt aktualisieren
      const wrap = document.getElementById(`slot-label-wrap-${_slotEditId}`);
      if (wrap) {
        const h3 = wrap.querySelector('.meal-title');
        const noteEl = wrap.querySelector('.meal-note');
        if (h3) h3.textContent = label;
        if (noteEl) noteEl.textContent = note;
      }
      closeSlotModal();
      showToast('✓ Bezeichnung gespeichert');
    } else {
      showToast(data.error || 'Fehler', 'error');
    }
  }
}

async function deleteSlot(slotId, planId, slotLabel) {
  if (!confirm(`Mahlzeit "${slotLabel}" wirklich entfernen?\nDie Rezeptauswahl für diesen Slot geht verloren.`)) return;
  const res = await fetch(`/plan/${planId}/slots/${slotId}`, { method: 'DELETE' });
  const data = await res.json();
  if (data.success) {
    const card = document.getElementById(`slot-${slotId}`);
    if (card) {
      card.style.transition = 'opacity .3s, max-height .4s';
      card.style.opacity = '0';
      card.style.overflow = 'hidden';
      setTimeout(() => { card.remove(); updateProgress(); }, 350);
    }
    showToast('🗑 Mahlzeit entfernt');
  } else {
    showToast('Fehler beim Entfernen', 'error');
  }
}

function closeSlotModal() {
  document.getElementById('slot-modal')?.classList.add('hidden');
  _slotEditId = null;
  _slotEditPlanId = null;
}

// ── Gekocht-Abhaken ────────────────────────────────────────────────────────────

async function toggleCooked(slotId, planId, btn) {
  const card = document.getElementById(`slot-${slotId}`);
  const data = await apiPost(`/plan/${planId}/cooked/${slotId}`);
  if (data.success) {
    if (data.cooked) {
      card?.classList.add('meal-card--cooked');
      btn.classList.add('cooked-btn--active');
      btn.textContent = '✅ Gekocht';
      btn.title = 'Als nicht gekocht markieren';
      showToast('✅ Als gekocht markiert');
    } else {
      card?.classList.remove('meal-card--cooked');
      btn.classList.remove('cooked-btn--active');
      btn.textContent = '☐ Gekocht';
      btn.title = 'Als gekocht markieren';
      showToast('Markierung entfernt');
    }
  }
}

// ── Portionen pro Slot ─────────────────────────────────────────────────────────

async function changePortions(slotId, planId, delta, btn) {
  const valEl = document.getElementById(`portions-val-${slotId}`);
  if (!valEl) return;
  const current = parseInt(valEl.textContent) || 2;
  const newVal = Math.max(1, Math.min(10, current + delta));
  if (newVal === current) return;

  valEl.textContent = newVal;
  btn.disabled = true;

  try {
    const data = await apiPost(`/plan/${planId}/slot-portions/${slotId}`, { portions: newVal });
    if (!data.success) {
      valEl.textContent = current;
      showToast('Fehler beim Speichern', 'error');
    } else {
      showToast(`🍽️ ${newVal} Portion${newVal !== 1 ? 'en' : ''} gesetzt`);
    }
  } catch(e) {
    valEl.textContent = current;
  }
  btn.disabled = false;
}

async function reorderPlan(planId, direction) {
  const data = await apiPost(`/plan/${planId}/reorder`, { direction });
  if (data.success) {
    showPageLoader('Wird sortiert…');
    requestAnimationFrame(() => requestAnimationFrame(() => location.reload()));
  } else {
    showToast(data.error || 'Fehler beim Verschieben', 'error');
  }
}

async function renamePlan(planId, currentName) {
  const newName = prompt('Neuer Name für diesen Plan:', currentName);
  if (!newName || !newName.trim() || newName.trim() === currentName) return;
  const data = await apiPost(`/plan/${planId}/rename`, { name: newName.trim() });
  if (data.success) {
    const el = document.getElementById(`plan-name-${planId}`);
    if (el) el.textContent = newName.trim();
    showToast('✓ Plan umbenannt');
  } else {
    showToast(data.error || 'Fehler beim Umbenennen', 'error');
  }
}

function showPlanLoading() {
  const btn = document.getElementById("gen-btn");
  const loading = document.getElementById("plan-loading");
  if (btn) { btn.disabled = true; btn.textContent = "⏳ Wird generiert…"; }
  if (loading) loading.style.display = "block";
  showPageLoader('Wochenplan wird erstellt…');
}
