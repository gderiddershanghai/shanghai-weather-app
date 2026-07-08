import { getContext, setContext } from 'svelte';
import copyJson from './copy.json';

export type Lang = 'en' | 'zh';

const copy = copyJson as Record<string, Partial<Record<Lang, string>>>;

export interface I18n {
	/** Current language (reactive: reads the layout's data prop through a closure). */
	readonly lang: Lang;
	/** Translate a copy key; falls back to English, then to the key itself. */
	t: (key: string) => string;
}

const I18N_KEY = Symbol('i18n');

/**
 * Create the i18n context object. `getLang` must read reactive state (e.g. the
 * layout's `data.lang`) so translations update when navigating /en <-> /zh.
 */
export function createI18n(getLang: () => Lang): I18n {
	return {
		get lang() {
			return getLang();
		},
		t: (key) => copy[key]?.[getLang()] ?? copy[key]?.en ?? key
	};
}

export function setI18n(i18n: I18n) {
	setContext(I18N_KEY, i18n);
}

export function getI18n(): I18n {
	return getContext<I18n>(I18N_KEY);
}
