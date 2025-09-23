export async function captureElementPNG(el: HTMLElement): Promise<string> {
  const { default: html2canvas } = await import('html2canvas');
  const canvas = await html2canvas(el, { backgroundColor: null, useCORS: true, logging: false });
  return canvas.toDataURL('image/png');
}
