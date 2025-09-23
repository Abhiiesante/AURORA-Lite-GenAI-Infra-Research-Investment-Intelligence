export type Parsed =
  | { mode: 'search'; term: string }
  | { mode: 'command'; cmd: string; args: string }
  | { mode: 'watchlist'; term: string }
  | { mode: 'topic'; term: string };

export function parseCommand(input: string): Parsed {
  const s = (input || '').trim();
  if (!s) return { mode: 'search', term: '' };
  const head = s[0];
  if (head === '>') {
    const rest = s.slice(1).trim();
    if (!rest) return { mode: 'command', cmd: '', args: '' };
    const parts = rest.split(/\s+/);
    // Command can be two words like "generate memo"
    const cmd = parts.slice(0, 2).join(' ');
    const args = parts.slice(2).join(' ');
    return { mode: 'command', cmd, args };
  }
  if (head === '@') {
    return { mode: 'watchlist', term: s.slice(1).trim() };
  }
  if (head === '#') {
    return { mode: 'topic', term: s.slice(1).trim() };
  }
  return { mode: 'search', term: s };
}
