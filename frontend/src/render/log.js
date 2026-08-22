// GET /today/log returns one row per meal item (joined with its parent
// meal), so items belonging to the same meal show up as separate rows with
// a shared meal_id. Group them back into meals before rendering.

export function renderLog(state) {
  const container = document.getElementById('mealLog');
  const { log } = state;

  if (!log.length) {
    container.innerHTML = '<p class="log__empty">Nothing logged yet today — your first entry will show up here.</p>';
    return;
  }

  const meals = new Map();
  for (const row of log) {
    if (!meals.has(row.meal_id)) {
      meals.set(row.meal_id, { raw_text: row.raw_text, logged_at: row.logged_at, items: [] });
    }
    meals.get(row.meal_id).items.push(row);
  }

  container.innerHTML = '';
  for (const meal of meals.values()) {
    const entry = document.createElement('div');
    entry.className = 'log__entry';

    const time = new Date(meal.logged_at).toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
    });

    const itemsHtml = meal.items
      .map((item) => {
        const cal = item.calories != null ? `${Math.round(item.calories)} kcal` : 'no nutrition match';
        return `<li>${escapeHtml(item.raw_name)} — ${cal}</li>`;
      })
      .join('');

    entry.innerHTML = `
      <p class="log__entry-time">${time}</p>
      <p class="log__entry-text">${escapeHtml(meal.raw_text)}</p>
      <ul class="log__entry-items">${itemsHtml}</ul>
    `;

    container.appendChild(entry);
  }
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}
