// Branded audio cues (tiny inline WAV data URIs). These are original minimal tones intended for UI feedback.
// ambient: soft low pad, hover: light tick, ping: chime, snap: shutter-like blip.

export const AUDIO_AMBIENT = 'data:audio/wav;base64,UklGRoQAAABXQVZFZm10IBAAAAABAAEAESsAACJWAAACABYAAAC0AAAADwAAACQAAABkYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYQ==';
export const AUDIO_HOVER = 'data:audio/wav;base64,UklGRHIAAABXQVZFZm10IBAAAAABAAEAESsAACJWAAACABYAAAB0AAAADQAAABUAAABmZmZmZmZmZmZmZmZmZmY=';
export const AUDIO_PING = 'data:audio/wav;base64,UklGRjQBAABXQVZFZm10IBAAAAABAAEAESsAACJWAAACABYAAADEAAAAGQAAADIAAACSkpKSkoqKioqKioqKioqKioqKioqKQ==';
export const AUDIO_SNAPSHOT = 'data:audio/wav;base64,UklGRkABAABXQVZFZm10IBAAAAABAAEAESsAACJWAAACABYAAAB+AAAADwAAAB8AAABhYWFmZmZqampnZ2dmZmZhYWE=';

// Prefer public files if available (apps/web/public/audio/*)
export const ambientSources = ['/audio/ambient.wav', AUDIO_AMBIENT];
export const hoverSources = ['/audio/hover.wav', AUDIO_HOVER];
export const pingSources = ['/audio/ping.wav', AUDIO_PING];
export const snapshotSources = ['/audio/snapshot.wav', AUDIO_SNAPSHOT];

// Note: For production, consider loading files from public/audio/*.wav instead for better quality and caching.
