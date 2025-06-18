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

document.getElementById("quickShuffleBtn").addEventListener("click", async () => {
  const collectionId = document.getElementById("collection").value;
  const res = await fetch("/api/shuffle-now", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ collectionId })
  });

  const result = await res.json();
  const statusText = document.getElementById("statusText");
  if (result.success) {
    statusText.textContent = `Shuffled ${result.shuffled} products!`;
  } else {
    statusText.textContent = "Shuffle failed.";
  }
});
document.getElementById("run").onclick = async ()=>{
  const smartId = document.getElementById("smartId").value;
  const customId = document.getElementById("customId").value;
  const title = document.getElementById("title").value;
  const res = await fetch("/api/mirror-shuffle", {
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body: JSON.stringify({ smartId, customId: customId||null, title })
  });
  const json = await res.json();
  if(json.success){
    document.getElementById("result").innerText =
      `Shuffled ${json.count} products into Custom Collection ID ${json.customId}`;
  } else document.getElementById("result").innerText = `Error`;
};