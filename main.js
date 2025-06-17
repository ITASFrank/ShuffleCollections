document.addEventListener("DOMContentLoaded", () => {
  const collectionSelect = document.getElementById("collection");
  const intervalSelect = document.getElementById("interval");
  const scheduleBtn = document.getElementById("scheduleBtn");
  const statusText = document.getElementById("statusText");

  fetch("/api/collections")
    .then(res => res.json())
    .then(data => {
      data.forEach(col => {
        const option = document.createElement("option");
        option.value = col.id;
        option.textContent = col.title;
        collectionSelect.appendChild(option);
      });
    });

  scheduleBtn.onclick = async () => {
    const res = await fetch("/api/schedule", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        collectionId: collectionSelect.value,
        interval: intervalSelect.value
      })
    });
    const json = await res.json();
    statusText.textContent = json.success ? "Scheduled" : "Failed";
  };
});
