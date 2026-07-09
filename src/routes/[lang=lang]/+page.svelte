<script lang="ts">
	// Story mode: intro, then the arrow/tap-driven step deck. Navigation lives
	// in the story store (goTo applies chart presets) — charts never know a
	// story exists.
	import { onMount } from 'svelte';
	import { getI18n } from '$lib/i18n';
	import StepDeck from '$lib/story/StepDeck.svelte';
	import StoryStep from '$lib/story/StoryStep.svelte';
	import StickyChart from '$lib/story/StickyChart.svelte';
	import {
		loadClimatology,
		loadCuratedEvents,
		loadDaily,
		loadMeta,
		loadOutliers,
		type Climatology,
		type CompactTable,
		type CuratedEvent,
		type Meta,
		type OutliersTable
	} from '$lib/data/load';
	import { base } from '$app/paths';

	const i18n = getI18n();

	let clim = $state<Climatology | null>(null);
	let outliers = $state<OutliersTable | null>(null);
	let curatedEvents = $state<CuratedEvent[]>([]);
	let meta = $state<Meta | null>(null);
	let daily = $state<CompactTable | null>(null);
	let monthly = $state<CompactTable | null>(null);
	let tempAqi = $state<(CompactTable & { binned: any[] }) | null>(null);
	let loadError = $state<string | null>(null);

	onMount(async () => {
		try {
			// hero payloads first (~60 KB gz) — chart paints immediately
			[clim, outliers, curatedEvents, meta] = await Promise.all([
				loadClimatology(),
				loadOutliers(),
				loadCuratedEvents(),
				loadMeta()
			]);
			// later-chapter payloads load behind the first paint
			const [d, m, ta] = await Promise.all([
				loadDaily(),
				fetch(`${base}/data/derived/monthly.json`).then((r) => r.json()),
				fetch(`${base}/data/derived/temp-aqi.json`).then((r) => r.json())
			]);
			daily = d;
			monthly = m;
			tempAqi = ta;
		} catch (e) {
			loadError = e instanceof Error ? e.message : String(e);
		}
	});

</script>

<section class="intro">
	<h1>{i18n.t('site.title')}</h1>
	<p class="tagline">{i18n.t('site.tagline')}</p>
	<p class="scroll-hint" aria-hidden="true">{i18n.t('story.scrollHint')} ↓</p>
</section>

{#if loadError}
	<p class="error">data failed to load: {loadError}</p>
{:else}
	<StepDeck>
		{#snippet graphic()}
			<StickyChart {clim} {outliers} {curatedEvents} {meta} {daily} {monthly} {tempAqi} />
		{/snippet}
		{#snippet step(id, _i, active)}
			<StoryStep copyKey="steps.{id}" {active} />
		{/snippet}
	</StepDeck>

	<section class="outro">
		<h2>{i18n.t('story.outroTitle')}</h2>
		<p>{i18n.t('story.outroBody')}</p>
		<a class="cta" href="explore/">{i18n.t('nav.explore')} →</a>
	</section>
{/if}

<style>
	.intro {
		min-height: 85svh;
		display: grid;
		place-content: center;
		text-align: center;
		gap: 0.75rem;
		padding: 1rem;
	}
	.intro h1 {
		font-size: clamp(2rem, 6vw, 3.5rem);
		margin: 0;
	}
	.tagline {
		color: var(--color-ink-muted);
		font-size: 1.1rem;
		margin: 0;
	}
	.scroll-hint {
		margin-top: 3rem;
		color: var(--color-ink-muted);
		animation: bob 2s ease-in-out infinite;
	}
	@media (prefers-reduced-motion: reduce) {
		.scroll-hint {
			animation: none;
		}
	}
	@keyframes bob {
		0%,
		100% {
			transform: translateY(0);
		}
		50% {
			transform: translateY(6px);
		}
	}
	.outro {
		min-height: 50svh;
		display: grid;
		place-content: center;
		text-align: center;
		gap: 0.75rem;
		padding: 2rem 1rem;
	}
	.cta {
		font-weight: 700;
	}
	.error {
		text-align: center;
		color: var(--color-hot);
		padding: 2rem;
	}
</style>
