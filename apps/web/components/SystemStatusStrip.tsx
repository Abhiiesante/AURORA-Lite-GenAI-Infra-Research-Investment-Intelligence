"use client";
import { useEffect, useState } from "react";

export default function SystemStatusStrip() {
  const [items, setItems] = useState([
    "GPU Cluster: 94% Utilized",
    "Funding Alerts: 3 Active",
    "New Startups: +12",
  ]);
  useEffect(() => {
    const id = setInterval(() => {
  setItems((prev: string[]) => {
        const nxt = [...prev];
        const t = nxt.shift();
        if (t) nxt.push(t);
        return nxt;
      });
    }, 4000);
    return () => clearInterval(id);
  }, []);
  return (
    <div className="ticker glass" role="status" aria-live="polite">
      <span>
        {items.join(" · ")}
      </span>
      <span>
        {items.join(" · ")}
      </span>
    </div>
  );
}
