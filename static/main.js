const smartSelect = document.getElementById("smartCollectionSelect");
const mirrorSelect = document.getElementById("manualCollectionSelect");
const mirrorName = document.getElementById("mirrorName");
const mirrorBtn = document.getElementById("mirrorBtn");
const shuffleBtn = document.getElementById("shuffleBtn");
const shuffleAllBtn = document.getElementById("shuffleAllBtn");
const statusText = document.getElementById("statusText");

fetch("/api/collections")
  .then(res => res.json())
  .then(data => {
    data.smart.forEach(c => {
      const opt = document.createElement("option");
      opt.value = c.id;
      opt.textContent = c.title;
      smartSelect.appendChild(opt);
    });

    data.manual.forEach(c => {
      const opt = document.createElement("option");
      opt.value = c.id;
      opt.textContent = c.title;
      mirrorSelect.appendChild(opt);
    });
  })
  .catch(err => {
    console.error("Error loading collections:", err);
    statusText.textContent = "Failed to load collections.";
  });

mirrorBtn.onclick = () => {
  const smartId = smartSelect.value;
  const manualId = mirrorSelect.value || null;
  const title = mirrorName.value || "Shuffle Mirror";

  fetch("/api/mirror", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ smart_id: smartId, manual_id: manualId, title })
  })
    .then(res => res.json())
    .then(res => {
      statusText.textContent = res.mirror_created
        ? "Mirror set! Now shuffle!"
        : res.error || "Error creating mirror.";
    });
};

shuffleBtn.onclick = () => {
  const smartId = smartSelect.value;
  const manualId = mirrorSelect.value;

  if (!smartId || !manualId) {
    statusText.textContent = "Please select both collections.";
    return;
  }

  fetch("/api/shuffle-now", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ collectionId: manualId })
  })
    .then(res => res.json())
    .then(res => {
      if (res.success) {
        statusText.textContent = "Shuffled successfully.";
      } else {
        statusText.textContent = res.error || "Failed to shuffle.";
      }
    });
};

shuffleAllBtn.onclick = () => {
  fetch("/api/shuffle-all", {
    method: "POST",
    headers: { "Content-Type": "application/json" }
  })
    .then(res => res.json())
    .then(res => {
      statusText.textContent = res.error ? res.error : "All collections shuffled.";
    });
};
