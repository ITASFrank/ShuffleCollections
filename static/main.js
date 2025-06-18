// main.js
const collectionSelect = document.getElementById("collectionSelect");
const shuffleBtn = document.getElementById("shuffleBtn");
const statusText = document.getElementById("statusText");

fetch("/api/collections")
  .then(res => res.json())
  .then(data => {
    [...data.smart, ...data.manual].forEach(c => {
      const opt = document.createElement("option");
      opt.value = c.id;
      opt.textContent = `${c.title} (${data.smart.some(s => s.id === c.id) ? 'Smart' : 'Manual'})`;
      collectionSelect.appendChild(opt);
    });
  })
  .catch(err => {
    console.error("Error loading collections:", err);
    statusText.textContent = "Failed to load collections.";
  });

shuffleBtn.onclick = () => {
  const colId = collectionSelect.value;
  if (!colId) {
    statusText.textContent = "Please select a collection.";
    return;
  }

  fetch("/api/shuffle-now", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ collectionId: colId })
  })
    .then(res => res.json())
    .then(res => {
      statusText.textContent = res.success
        ? "Shuffled successfully."
        : res.error || "Failed to shuffle.";
    });
};
