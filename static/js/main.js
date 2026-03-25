/* ═══════════════════════════════════════════════════════════════
   Meal Planner – JavaScript
   ═══════════════════════════════════════════════════════════════ */

'use strict';

// ── Loading-State für Formulare ────────────────────────────────────────────────

function setLoading(form, loadingText) {
  const btn = form.querySelector('button[type="submit"]');
  if (btn) {
    btn.disabled = true;
    btn.dataset.originalText = btn.textContent;
    btn.textContent = loadingText || '⏳ Bitte warten…';
  }
  // Timeout-Fallback: nach 60s wieder aktivieren falls kein Reload
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
  return res.json();
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
  const pct = Math.round((done / total) * 100);

  const fill = document.querySelector('.progress-fill');
  if (fill) fill.style.width = pct + '%';

  const label = document.querySelector('.progress-label');
  if (label) label.textContent = `${done}/${total} Gerichte gewählt`;

  // Abschluss-Alert anzeigen wenn fertig
  if (done === total) {
    const existing = document.querySelector('.finish-alert');
    if (!existing && typeof PLAN_ID !== 'undefined') {
      const alert = document.createElement('div');
      alert.className = 'alert alert--success finish-alert';
      alert.innerHTML = `
        <strong>🎉 Alle Gerichte ausgewählt!</strong>
        <form action="/plan/${PLAN_ID}/finish" method="POST" style="display:inline">
          <button class="btn btn--primary btn--sm" type="submit">🛒 Einkaufsliste erstellen →</button>
        </form>
      `;
      document.querySelector('.planning-grid').before(alert);
    }
  }
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
});

// Flash messages auto-dismiss
setTimeout(() => {
  document.querySelectorAll('.flash').forEach(f => {
    f.style.transition = 'opacity .4s ease';
    f.style.opacity = '0';
    setTimeout(() => f.remove(), 400);
  });
}, 5000);

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

function showPlanLoading() {
  const btn = document.getElementById("gen-btn");
  const loading = document.getElementById("plan-loading");
  if (btn) { btn.disabled = true; btn.textContent = "⏳ Wird generiert…"; }
  if (loading) loading.style.display = "block";
}
