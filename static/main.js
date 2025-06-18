const smartSelect = document.getElementById("smartSelect");
const mirrorSelect = document.getElementById("mirrorSelect");
const mirrorName = document.getElementById("mirrorName");
const mirrorBtn = document.getElementById("mirrorBtn");
const shuffleBtn = document.getElementById("shuffleBtn");
const statusText = document.getElementById("statusText");

let allCollections = [];

fetch("/api/collections")
  .then(res => res.json())
  .then(data => {
    allCollections = data;
    data.forEach(col => {
      const opt = document.createElement("option");
      opt.value = col.id;
      opt.textContent = `${col.title} (${col.id})`;
      if (col.rules) smartSelect.appendChild(opt);
      else mirrorSelect.appendChild(opt.cloneNode(true));
    });
  });

mirrorBtn.onclick = () => {
  const smartId = smartSelect.value;
  const manualId = mirrorSelect.value || null;
  const title = mirrorName.value || "Shuffle Mirror";

  fetch("/api/mirror", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({ smart_id: smartId, manual_id: manualId, title })
  })
    .then(res => res.json())
    .then(res => {
      if (res.mirror_created) {
        statusText.textContent = "Mirror set! Now shuffle!";
      } else {
        statusText.textContent = res.error || "Error creating mirror.";
      }
    });
};

shuffleBtn.onclick = () => {
  const smartId = smartSelect.value;
  fetch("/api/shuffle-now", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({ smart_id: smartId })
  })
    .then(res => res.json())
    .then(res => {
      if (res.success) {
        statusText.textContent = `Shuffled ${res.products_shuffled} products!`;
      } else {
        statusText.textContent = res.error || "Failed to shuffle.";
      }
    });
};
