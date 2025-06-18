const smartSelect = document.getElementById("smartCollectionSelect");
const mirrorSelect = document.getElementById("manualCollectionSelect");
const mirrorName = document.getElementById("mirrorName");
const mirrorBtn = document.getElementById("mirrorBtn");
const shuffleBtn = document.getElementById("shuffleBtn");
const statusText = document.getElementById("statusText");

// Fetch and populate collection dropdowns
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

// Mirror creation logic
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
  const manualId = mirrorSelect.value;
  if (!manualId || manualId === "-- Create New --") {
    statusText.textContent = "Please select a valid mirror collection.";
    return;
  }

fetch("/api/shuffle-now", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    smart_id: document.getElementById("smartCollectionSelect").value,
    manual_id: document.getElementById("manualCollectionSelect").value
  })
});
};

