async function fetchCollections() {
  const res = await fetch("/api/collections");
  const collections = await res.json();
  const smart = collections.filter(c => c.type === "smart");
  const manual = collections.filter(c => c.type === "manual");

  const smartSelect = document.getElementById("smartSelect");
  const mirrorSelect = document.getElementById("mirrorSelect");

  smart.forEach(c => {
    const opt = document.createElement("option");
    opt.value = c.id;
    opt.textContent = c.title;
    smartSelect.appendChild(opt);
  });

  manual.forEach(c => {
    const opt = document.createElement("option");
    opt.value = c.id;
    opt.textContent = c.title;
    mirrorSelect.appendChild(opt);
  });
}

document.getElementById("shuffleBtn").addEventListener("click", async () => {
  const smartId = document.getElementById("smartSelect").value;
  const mirrorId = document.getElementById("mirrorSelect").value;
  const mirrorTitle = document.getElementById("mirrorTitle").value;
  const status = document.getElementById("status");

  const body = {
    smart_id: smartId,
    mirror_id: mirrorId || null,
    mirror_title: mirrorTitle || "Shuffled Collection"
  };

  const res = await fetch("/api/mirror-shuffle", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });

  const data = await res.json();
  status.textContent = data.success ? "Shuffling complete!" : `Error: ${data.error}`;
});

window.onload = fetchCollections;
