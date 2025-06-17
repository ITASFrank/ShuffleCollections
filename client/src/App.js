import { useState, useEffect } from "react";

export default function ShuffleSchedulerApp() {
  const [collections, setCollections] = useState([]);
  const [selectedCollection, setSelectedCollection] = useState("");
  const [interval, setInterval] = useState("hourly");
  const [status, setStatus] = useState(null);

  useEffect(() => {
    fetch("/api/collections")
      .then((res) => res.json())
      .then((data) => setCollections(data))
      .catch(() => setCollections([]));
  }, []);

  const handleSchedule = async () => {
    const res = await fetch("/api/schedule", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        collectionId: selectedCollection,
        interval,
      }),
    });
    const result = await res.json();
    setStatus(result.success ? "Scheduled" : "Failed");
  };

  return (
    <div className="p-6 max-w-xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">🌀 Shuffle Collection Scheduler</h1>
      <div className="space-y-4">
        <div>
          <label htmlFor="collection">Select Collection</label>
          <select id="collection" onChange={(e) => setSelectedCollection(e.target.value)}>
            {collections.map((col) => (
              <option key={col.id} value={col.id}>{col.title}</option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="interval">Shuffle Interval</label>
          <select id="interval" onChange={(e) => setInterval(e.target.value)} defaultValue="hourly">
            <option value="hourly">Hourly</option>
            <option value="daily">Daily</option>
            <option value="weekly">Weekly</option>
          </select>
        </div>
        <button onClick={handleSchedule}>Set Shuffle</button>
        {status && <p>{status}</p>}
      </div>
    </div>
  );
}
