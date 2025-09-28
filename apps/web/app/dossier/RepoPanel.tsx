"use client";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

export type Repo = { url: string; stars?: number };

// Clean minimal implementation (previous version was corrupted by a pasted build log)
export function RepoPanel({ repos, onAddToMemo }: { repos?: Repo[]; onAddToMemo?: (item: { title: string; source?: string }) => void }) {
  const firstRepo = useMemo(() => (repos && repos.length ? repos[0] : undefined), [repos]);
  const [active, setActive] = useState(firstRepo);
  const [showCode, setShowCode] = useState(false);
  const dialogHeaderId = useRef(`repo-panel-dialog-title-${Math.random().toString(36).slice(2)}`);

  useEffect(() => {
    if (!active && firstRepo) setActive(firstRepo);
  }, [firstRepo, active]);

  const safePathname = useCallback((u?: string) => {
    try {
      if (!u) return "";
      return new URL(u).pathname.replace(/^\/+/, "");
    } catch {
      return u || "";
    }
  }, []);

  const fakeDiff = `diff --git a/src/index.ts b/src/index.ts\n+ export const hello = () => 'hello';\n- export const bye = () => 'bye';`;
  const fakeCommits = [
    { id: "c1", message: "feat: add embeddings endpoint", url: "#" },
    { id: "c2", message: "fix: retry on 429", url: "#" },
    { id: "c3", message: "chore: bump deps", url: "#" },
  ];

  const onEscClose = useCallback((e: React.KeyboardEvent) => {
    if (e.key === "Escape") {
      e.stopPropagation();
      setShowCode(false);
    }
  }, []);

  return (
    <div>
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        {repos?.map(r => (
          <button
            key={r.url}
            type="button"
            aria-label={`Select repository ${safePathname(r.url)}`}
            className="magnetic"
            style={{ padding: "6px 10px", borderRadius: 8, border: "1px solid rgba(255,255,255,0.16)", background: "transparent" }}
            onClick={() => setActive(r)}
          >
            {safePathname(r.url)} {typeof r.stars === "number" && `⭐${r.stars}`}
          </button>
        ))}
      </div>
      {active && (
        <div style={{ marginTop: 8 }}>
          <div style={{ fontSize: 12, opacity: 0.85 }}>
            Selected: <a href={active.url} target="_blank" rel="noopener noreferrer">{active.url}</a>
          </div>
          <div className="row" style={{ marginTop: 8, gap: 8 }}>
            <button
              type="button"
              aria-haspopup="dialog"
              aria-controls={dialogHeaderId.current}
              className="magnetic"
              onClick={() => setShowCode(true)}
              style={{ padding: "6px 10px", borderRadius: 8, border: "1px solid rgba(255,255,255,0.16)", background: "transparent" }}
            >
              View code
            </button>
            <a
              className="magnetic"
              href={active.url}
              target="_blank"
              rel="noopener noreferrer"
              style={{ padding: "6px 10px", borderRadius: 8, border: "1px solid rgba(255,255,255,0.16)", background: "transparent" }}
            >
              Open in GitHub
            </a>
            {onAddToMemo && (
              <button
                type="button"
                className="magnetic"
                onClick={() => onAddToMemo({ title: `Repo: ${safePathname(active.url)}`, source: active.url })}
                style={{ padding: "6px 10px", borderRadius: 8, border: "1px solid rgba(255,255,255,0.16)", background: "transparent" }}
              >
                Add to memo
              </button>
            )}
          </div>
          <div style={{ marginTop: 8 }}>
            <div style={{ fontSize: 12, opacity: 0.8, marginBottom: 4 }}>Recent commits</div>
            <ul style={{ fontSize: 12, lineHeight: 1.8 }}>
              {fakeCommits.map(c => (
                <li key={c.id}>
                  <a
                    href={c.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{ textDecoration: "none", color: "inherit" }}
                  >
                    {c.message}
                  </a>
                  {onAddToMemo && (
                    <button
                      type="button"
                      className="magnetic"
                      onClick={() => onAddToMemo({ title: `Commit: ${c.message}`, source: active.url })}
                      style={{
                        marginLeft: 8,
                        padding: "2px 6px",
                        borderRadius: 6,
                        border: "1px solid rgba(255,255,255,0.16)",
                        background: "transparent",
                        fontSize: 11,
                      }}
                    >
                      Add to memo
                    </button>
                  )}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
      {showCode && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby={dialogHeaderId.current}
          className="cmdk-overlay"
          onClick={() => setShowCode(false)}
          onKeyDown={onEscClose}
        >
          <div className="cmdk-panel" onClick={e => e.stopPropagation()} style={{ gridTemplateColumns: "1fr" }}>
            <header className="row" style={{ justifyContent: "space-between" }}>
              <h3 id={dialogHeaderId.current} style={{ margin: 0 }}>Code viewer</h3>
              <button type="button" aria-label="Close code viewer" onClick={() => setShowCode(false)}>
                Close
              </button>
            </header>
            <pre className="glass" style={{ padding: 12, whiteSpace: "pre-wrap", fontSize: 12 }}>{fakeDiff}</pre>
          </div>
        </div>
      )}
    </div>
  );
}
