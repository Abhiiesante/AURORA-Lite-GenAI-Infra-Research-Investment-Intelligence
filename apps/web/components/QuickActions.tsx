"use client";

const items = [
  { href: "/market-map", label: "Market Map", hint: "See clusters & segments" },
  { href: "/trends", label: "Trends", hint: "Signals over time" },
  { href: "/compare", label: "Compare", hint: "Side-by-side companies" },
  { href: "/kg", label: "KG Explorer", hint: "Query the graph" },
];

export default function QuickActions() {
  return (
    <div className="quick" role="list" aria-label="Quick actions">
      {items.map(i => (
        <a key={i.href} href={i.href} className="card glass" role="listitem" aria-label={`${i.label}. ${i.hint}`}>
          <div>
            <div style={{ fontWeight: 600 }}>{i.label}</div>
            <div style={{ opacity: 0.7, fontSize: 12 }}>{i.hint}</div>
          </div>
          <div style={{ opacity: 0.8 }}>→</div>
        </a>
      ))}
    </div>
  );
}
