// Manual date/number formatting (avoids Intl edge cases in WeChat's webview).

import type { Lang } from '$lib/i18n';

const MONTHS_EN = [
	'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
	'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
];

/** '2016-01-24' -> 'Jan 24, 2016' / '2016年1月24日' */
export function formatDate(iso: string, lang: Lang): string {
	const [y, m, d] = iso.split('-').map(Number);
	if (lang === 'zh') return `${y}年${m}月${d}日`;
	return `${MONTHS_EN[m - 1]} ${d}, ${y}`;
}

/** DOY month tick label */
export function monthLabel(monthIndex0: number, lang: Lang): string {
	if (lang === 'zh') return `${monthIndex0 + 1}月`;
	return MONTHS_EN[monthIndex0];
}

export function formatTemp(value: number | null, withUnit = true): string {
	if (value == null) return '–';
	return `${value.toFixed(1)}${withUnit ? '°C' : ''}`;
}
