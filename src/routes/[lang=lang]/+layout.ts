import type { LayoutLoad } from './$types';
import type { Lang } from '$lib/i18n';

export const load: LayoutLoad = ({ params }) => {
	return { lang: params.lang as Lang };
};
