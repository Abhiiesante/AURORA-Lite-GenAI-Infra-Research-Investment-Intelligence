export async function rasterizeSvgToPngDataUrl(svgStr: string, width: number, height: number): Promise<string> {
  return new Promise((resolve, reject) => {
    const svg = new Blob([svgStr], { type: 'image/svg+xml' });
    const url = URL.createObjectURL(svg);
    const img = new Image();
    img.onload = () => {
      try {
        const canvas = document.createElement('canvas');
        canvas.width = width; canvas.height = height;
        const ctx = canvas.getContext('2d');
        if (!ctx) throw new Error('no ctx');
        ctx.drawImage(img, 0, 0, width, height);
        const dataUrl = canvas.toDataURL('image/png');
        URL.revokeObjectURL(url);
        resolve(dataUrl);
      } catch (e){
        URL.revokeObjectURL(url);
        reject(e);
      }
    };
    img.onerror = (e) => { URL.revokeObjectURL(url); reject(e); };
    img.src = url;
  });
}

export async function exportCompareBundle(opts: {
  host: HTMLElement;
  svgStr: string;
  width: number;
  height: number;
  meta: any;
}){
  const { host, svgStr, width, height, meta } = opts;
  const { jsPDF } = await import('jspdf');
  const html2canvas = (await import('html2canvas')).default;
  const canvas = await html2canvas(host, { backgroundColor: null, useCORS: true, logging: false });
  const heroPng = canvas.toDataURL('image/png');
  const overlayPng = await rasterizeSvgToPngDataUrl(svgStr, width, height);
  const pdf = new jsPDF({ unit:'px', format:[width, height] });
  pdf.addImage(heroPng, 'PNG', 0, 0, width, height);
  pdf.addPage([width, height], 'portrait');
  pdf.addImage(overlayPng, 'PNG', 0, 0, width, height);
  pdf.addPage([width, height], 'portrait');
  pdf.setFontSize(14);
  pdf.text('Comparator — Provenance', 20, 28);
  pdf.setFontSize(11);
  const lines = JSON.stringify(meta, null, 2).split('\n');
  let y = 48;
  for (const line of lines){
    if (y > height - 24){ pdf.addPage([width, height], 'portrait'); y = 28; }
    pdf.text(line.substring(0, 120), 20, y);
    y += 16;
  }
  const fname = `compare_bundle_${Date.now()}.pdf`;
  pdf.save(fname);
  // Also offer the JSON as a sidecar
  try{
    const blob = new Blob([JSON.stringify(meta, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = fname.replace(/\.pdf$/, '.json'); a.click();
    URL.revokeObjectURL(url);
  } catch {}
}
