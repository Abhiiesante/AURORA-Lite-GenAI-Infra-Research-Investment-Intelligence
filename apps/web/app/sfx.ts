"use client";
import { Howl } from "howler";
import { useSfxStore } from "./sfxStore";

function toneToDataURI(freq = 440, durationMs = 120, type: OscillatorType = "sine"): string {
  const sampleRate = 44100; const length = Math.max(1, Math.floor((durationMs/1000)*sampleRate));
  const attack = Math.floor(0.04*sampleRate); const release = Math.floor(0.12*sampleRate);
  const data = new Float32Array(length);
  for (let i=0;i<length;i++){
    const t = i/sampleRate; let v = Math.sin(2*Math.PI*freq*t);
    if (type === 'square') v = Math.sign(v);
    else if (type === 'triangle') v = 2*Math.asin(Math.sin(2*Math.PI*freq*t))/Math.PI;
    else if (type === 'sawtooth') v = 2*(t*freq - Math.floor(0.5 + t*freq));
    // Envelope
    let env = 1.0;
    if (i < attack) env = i/attack;
    if (i > length - release) env = Math.max(0, (length - i) / release);
    data[i] = v * env * 0.6;
  }
  // Convert to WAV PCM 16-bit
  const buffer = new ArrayBuffer(44 + length*2);
  const view = new DataView(buffer);
  const writeStr = (o: number, s: string) => { for(let i=0;i<s.length;i++) view.setUint8(o+i, s.charCodeAt(i)); };
  writeStr(0, 'RIFF'); view.setUint32(4, 36 + length*2, true); writeStr(8, 'WAVE');
  writeStr(12, 'fmt '); view.setUint32(16, 16, true); view.setUint16(20, 1, true); view.setUint16(22, 1, true); view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate*2, true); view.setUint16(32, 2, true); view.setUint16(34, 16, true);
  writeStr(36, 'data'); view.setUint32(40, length*2, true);
  let off = 44; for (let i=0;i<length;i++){ let s = Math.max(-1, Math.min(1, data[i])); view.setInt16(off, s<0? s*0x8000 : s*0x7FFF, true); off += 2; }
  const blob = new Blob([buffer], { type: 'audio/wav' });
  return URL.createObjectURL(blob);
}

function play(src: string){
  const { enabled, volume } = useSfxStore.getState();
  if (!enabled) return;
  const h = new Howl({ src: [src], volume }); h.play();
}

export const sfx = {
  open() { play(toneToDataURI(480, 110, 'triangle')); },
  close() { play(toneToDataURI(360, 90, 'sine')); },
  move() { play(toneToDataURI(520, 60, 'square')); },
  confirm() { play(toneToDataURI(620, 120, 'sawtooth')); },
};
