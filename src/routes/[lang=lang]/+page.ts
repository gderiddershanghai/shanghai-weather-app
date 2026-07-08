import type { EntryGenerator } from './$types';

// Guarantee both language trees are prerendered even though the static root
// only links to them via a JS redirect. /[lang]/explore/ is then discovered
// by the prerender crawler through the header links.
export const entries: EntryGenerator = () => [{ lang: 'en' }, { lang: 'zh' }];
