"use client";
import { useEffect, useRef, useState } from "react";
import axios from "axios";
import jsPDF from "jspdf";
import html2canvas from "html2canvas";

const api = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function DealsPage() {
  const [cands, setCands] = useState([] as any[]);
  const [memo, setMemo] = useState(null as any | null);
  const memoRef = useRef(null as HTMLDivElement | null);

  useEffect(() => {
    axios.get(`${api}/deals/candidates`).then((res: any) => setCands(res.data.candidates || [])).catch(() => setCands([]));
  }, []);

  const genMemo = async (company_id: number) => {
    const r = await axios.post(`${api}/deals/memo`, { company_id });
    setMemo(r.data);
  };

  const exportPDF = async () => {
    if (!memoRef.current) return;
    const canvas = await html2canvas(memoRef.current);
    const img = canvas.toDataURL("image/png");
    const pdf = new jsPDF({ unit: "pt", format: "a4" });
    const width = pdf.internal.pageSize.getWidth();
    const ratio = width / canvas.width;
    pdf.addImage(img, "PNG", 0, 0, canvas.width * ratio, canvas.height * ratio);
    pdf.save("memo.pdf");
  };

  return (
    <div style={{ padding: 16 }}>
      <h2>Deal Room</h2>
      <div style={{ display: 'flex', gap: 16 }}>
        <div style={{ flex: 1 }}>
          <h3>Candidates</h3>
          <ul>
            {cands.map((c: any) => (
              <li key={c.company_id} style={{ marginBottom: 8 }}>
                <span>#{c.company_id}</span>
                <span style={{ marginLeft: 8 }}>Score: {c.score}</span>
                <button onClick={() => genMemo(c.company_id)} style={{ marginLeft: 8, border: '1px solid #ddd', background: '#f5f5f5', padding: '2px 6px' }}>Generate Memo</button>
              </li>
            ))}
          </ul>
        </div>
        <div style={{ flex: 1 }}>
          <h3>Memo</h3>
          <div ref={memoRef} style={{ border: '1px solid #eee', padding: 12, minHeight: 240 }}>
            {memo ? (
              <div>
                <div>Company: {memo.company_id}</div>
                <ul>
                  {(memo.one_pager?.bullets || []).map((b: string, i: number) => (<li key={i}>{b}</li>))}
                </ul>
                <div style={{ fontSize: 12, color: '#666' }}>Sources: {(memo.sources || []).length}</div>
              </div>
            ) : (
              <div>Generate a memo to preview here.</div>
            )}
          </div>
          <button onClick={exportPDF} style={{ marginTop: 8, border: '1px solid #ddd', background: '#f5f5f5', padding: '4px 8px' }}>Export PDF</button>
        </div>
      </div>
    </div>
  );
}
