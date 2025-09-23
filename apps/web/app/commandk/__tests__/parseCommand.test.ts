import { parseCommand } from "../../commandk/parseCommand";

describe('parseCommand', () => {
  it('parses plain query', () => {
    expect(parseCommand('pinecone')).toEqual({ kind: 'query', q: 'pinecone' });
  });
  it('parses generate memo cmd', () => {
    expect(parseCommand('>generate memo pinecone')).toEqual({ kind: 'cmd', name: 'generate', args: 'memo pinecone' });
  });
  it('parses watchlist', () => {
    expect(parseCommand('@watchlist ai')).toEqual({ kind: 'watch', list: 'watchlist ai' });
  });
  it('parses topic', () => {
    expect(parseCommand('#vector db')).toEqual({ kind: 'topic', topic: 'vector db' });
  });
});
