export function renderTotals(state) {
  const { totals } = state;

  document.getElementById('totalCalories').textContent = `${Math.round(totals.calories)} kcal`;
  document.getElementById('totalProtein').textContent = `${Math.round(totals.protein_g)} g`;
  document.getElementById('totalCarbs').textContent = `${Math.round(totals.carbs_g)} g`;
  document.getElementById('totalFat').textContent = `${Math.round(totals.fat_g)} g`;
}
