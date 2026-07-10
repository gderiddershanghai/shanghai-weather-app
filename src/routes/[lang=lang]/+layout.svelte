<script lang="ts">
	import { page } from '$app/state';
	import { base } from '$app/paths';
	import { createI18n, setI18n } from '$lib/i18n';
	import '../../app.css';

	let { data, children } = $props();

	const i18n = createI18n(() => data.lang);
	setI18n(i18n);

	// Same page in the other language: swap the /en/ or /zh/ segment inside the
	// full pathname (which already includes any deployment base path). Never
	// string-concat `base` with pathnames — with paths.relative it's '..'-style.
	const otherLang = $derived(data.lang === 'en' ? 'zh' : 'en');
	const switchHref = $derived(page.url.pathname.replace(/\/(en|zh)(\/|$)/, `/${otherLang}$2`));
	const onExplore = $derived(page.url.pathname.includes('/explore/'));
</script>

<svelte:head>
	<title>{i18n.t('site.title')}</title>
	<meta name="description" content={i18n.t('site.tagline')} />
	<meta property="og:title" content={i18n.t('site.title')} />
	<meta property="og:locale" content={data.lang === 'zh' ? 'zh_CN' : 'en_US'} />
	<link
		rel="alternate"
		hreflang="en"
		href={page.url.pathname.replace(/\/(en|zh)(\/|$)/, '/en$2')}
	/>
	<link
		rel="alternate"
		hreflang="zh"
		href={page.url.pathname.replace(/\/(en|zh)(\/|$)/, '/zh$2')}
	/>
</svelte:head>

<header class="site-header">
	<a class="wordmark" href="{base}/{data.lang}/">{i18n.t('site.title')}</a>
	<nav>
		<a href="{base}/{data.lang}/" class:active={!onExplore}>{i18n.t('nav.story')}</a>
		<a href="{base}/{data.lang}/explore/" class:active={onExplore}>{i18n.t('nav.explore')}</a>
		<a href={switchHref} lang={otherLang} data-sveltekit-reload>{i18n.t('nav.switchLang')}</a>
	</nav>
</header>

<main>
	{@render children()}
</main>

<footer class="site-footer">
	<p>{i18n.t('footer.source')}</p>
</footer>

<style>
	.site-header {
		display: flex;
		align-items: baseline;
		justify-content: space-between;
		gap: 1rem;
		padding: 0.75rem 1rem;
		border-bottom: 1px solid var(--color-border);
	}
	.wordmark {
		font-weight: 700;
		text-decoration: none;
		color: var(--color-ink);
	}
	nav {
		display: flex;
		gap: 1rem;
	}
	nav a {
		color: var(--color-ink-muted);
		text-decoration: none;
	}
	nav a.active {
		color: var(--color-ink);
		font-weight: 600;
	}
	.site-footer {
		padding: 2rem 1rem;
		color: var(--color-ink-muted);
		font-size: 0.85rem;
		text-align: center;
	}
</style>
