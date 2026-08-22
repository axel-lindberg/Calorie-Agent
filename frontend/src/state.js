// Small in-memory store. No framework needed for this much state - a plain
// object plus a subscribe/notify list is enough for a single-page app with
// three pieces of data (totals, log, form status).

const state = {
  totals: { calories: 0, protein_g: 0, carbs_g: 0, fat_g: 0 },
  log: [],
};

const listeners = new Set();

export function getState() {
  return state;
}

export function setState(partial) {
  Object.assign(state, partial);
  for (const listener of listeners) {
    listener(state);
  }
}

export function subscribe(listener) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}
