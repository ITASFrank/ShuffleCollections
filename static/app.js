import { useState, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Select, SelectItem } from "@/components/ui/select";

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
      <Card className="mb-4">
        <CardContent className="space-y-4 p-4">
          <div>
            <Label htmlFor="collection">Select Collection</Label>
            <Select id="collection" onValueChange={setSelectedCollection}>
              {collections.map((col) => (
                <SelectItem key={col.id} value={col.id}>{col.title}</SelectItem>
              ))}
            </Select>
          </div>
          <div>
            <Label htmlFor="interval">Shuffle Interval</Label>
            <Select id="interval" onValueChange={setInterval} defaultValue="hourly">
              <SelectItem value="hourly">Hourly</SelectItem>
              <SelectItem value="daily">Daily</SelectItem>
              <SelectItem value="weekly">Weekly</SelectItem>
            </Select>
          </div>
          <Button onClick={handleSchedule}>Set Shuffle</Button>
          {status && <p className="text-sm text-gray-500">{status}</p>}
        </CardContent>
      </Card>
    </div>
  );
}
