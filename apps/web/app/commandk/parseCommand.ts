export type ParsedCommand =
  | { kind: 'cmd'; name: string; args: string }
  | { kind: 'watch'; list: string }
  | { kind: 'topic'; topic: string }
  | { kind: 'query'; q: string };

export function parseCommand(input: string): ParsedCommand {
  const s = (input || '').trim();
  if (s.startsWith('>')) {
    const rest = s.slice(1).trim();
    const [name, ...restParts] = rest.split(/\s+/);
    return { kind: 'cmd', name: name || '', args: restParts.join(' ') };
  }
  if (s.startsWith('@')) {
    return { kind: 'watch', list: s.slice(1).trim() };
  }
  if (s.startsWith('#')) {
    return { kind: 'topic', topic: s.slice(1).trim() };
  }
  return { kind: 'query', q: s };
}
