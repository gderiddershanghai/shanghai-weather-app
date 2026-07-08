import type { EntryGenerator } from './$types';

// Explicit (belt-and-braces alongside crawler discovery via header links).
export const entries: EntryGenerator = () => [{ lang: 'en' }, { lang: 'zh' }];
