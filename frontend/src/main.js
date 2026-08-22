import './styles.css';

import { getTodaysTotals, getTodaysLog } from './api.js';
import { setState, subscribe } from './state.js';
import { renderTotals } from './render/totals.js';
import { renderLog } from './render/log.js';
import { initEntryForm } from './render/entryForm.js';

async function refresh() {
  const [totals, log] = await Promise.all([getTodaysTotals(), getTodaysLog()]);
  setState({ totals, log });
}

// Every state change re-runs both render functions. Cheap enough at this
// scale - no need for a virtual DOM or fine-grained diffing.
subscribe((state) => {
  renderTotals(state);
  renderLog(state);
});

initEntryForm(refresh);

refresh().catch((err) => {
  console.error('Failed to load today\'s data', err);
});
