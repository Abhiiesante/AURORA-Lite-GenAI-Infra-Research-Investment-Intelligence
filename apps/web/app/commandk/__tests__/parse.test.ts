import { parseCommand } from "../parseCommand";

describe('parseCommand (compat)', () => {
  it('parses empty as query', () => {
    expect(parseCommand('')).toEqual({ kind: 'query', q: '' });
  });
  it('parses search term', () => {
    expect(parseCommand('pinecone')).toEqual({ kind: 'query', q: 'pinecone' });
  });
  it('parses command with args', () => {
    expect(parseCommand('>generate memo pinecone')).toEqual({ kind: 'cmd', name: 'generate', args: 'memo pinecone' });
  });
  it('parses watchlist', () => {
    expect(parseCommand('@openai')).toEqual({ kind: 'watch', list: 'openai' });
  });
  it('parses topic', () => {
    expect(parseCommand('#vector')).toEqual({ kind: 'topic', topic: 'vector' });
  });
});
