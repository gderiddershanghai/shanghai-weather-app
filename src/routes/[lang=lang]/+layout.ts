import type { EntryGenerator, LayoutLoad } from './$types';
import type { Lang } from '$lib/i18n';

// Guarantee both language trees are prerendered even though the static root
// only links to them via a JS redirect.
export const entries: EntryGenerator = () => [{ lang: 'en' }, { lang: 'zh' }];

export const load: LayoutLoad = ({ params }) => {
	return { lang: params.lang as Lang };
};
