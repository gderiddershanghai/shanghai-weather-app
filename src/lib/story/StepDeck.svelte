<script lang="ts">
	// Arrow/tap-driven story deck (replaces the scroll-driven Scrolly).
	// Copy lives in a dedicated rail (desktop) / bottom sheet (mobile) so it
	// can NEVER cover the chart. Navigation: ← → keys, tap zones on the chart's
	// outer edges, horizontal swipe, and the progress bar's buttons.
	import { onMount, type Snippet } from 'svelte';
	import { get } from 'svelte/store';
	import { activeStepIndex, next, prev, restoreFromHash } from '$lib/stores/story';
	import { steps } from './steps';
	import { getI18n } from '$lib/i18n';
	import StoryProgress from './StoryProgress.svelte';

	let {
		graphic,
		step
	}: {
		graphic: Snippet;
		/** renders one step's copy; receives (id, index, active) */
		step: Snippet<[string, number, boolean]>;
	} = $props();

	const i18n = getI18n();

	let deckEl: HTMLElement | null = $state(null);

	onMount(() => {
		restoreFromHash();
		const onHash = () => restoreFromHash();
		window.addEventListener('hashchange', onHash);

		// Scroll navigation — coexists with arrows/taps/swipe, never replaces
		// them. Wheel over the deck advances/retreats steps (debounced); at the
		// first/last step the event is NOT captured, so normal page scrolling
		// resumes and the reader can reach the intro above / outro below.
		let wheelLock = 0;
		const onWheel = (e: WheelEvent) => {
			if (Math.abs(e.deltaY) < 24) return; // ignore trackpad jitter
			const i = get(activeStepIndex);
			const releasing = (e.deltaY > 0 && i === steps.length - 1) || (e.deltaY < 0 && i === 0);
			if (releasing) return; // hand back to page scroll at the ends
			e.preventDefault();
			const now = Date.now();
			if (now - wheelLock < 650) return;
			wheelLock = now;
			if (e.deltaY > 0) next();
			else prev();
		};
		// manual listener: must be non-passive to preventDefault
		deckEl?.addEventListener('wheel', onWheel, { passive: false });

		return () => {
			window.removeEventListener('hashchange', onHash);
			deckEl?.removeEventListener('wheel', onWheel);
		};
	});

	function onKeydown(e: KeyboardEvent) {
		if (e.metaKey || e.ctrlKey || e.altKey) return;
		const target = e.target as HTMLElement | null;
		if (target && /^(INPUT|TEXTAREA|SELECT)$/.test(target.tagName)) return;
		switch (e.key) {
			case 'ArrowRight':
			case 'PageDown':
				e.preventDefault();
				next();
				break;
			case 'ArrowLeft':
			case 'PageUp':
				e.preventDefault();
				prev();
				break;
			case 'Home':
				e.preventDefault();
				import('$lib/stores/story').then((m) => m.goTo(0));
				break;
		}
	}

	// swipe: strongly-horizontal gestures on the chart region navigate
	let swipeStart: { x: number; y: number } | null = null;
	function onPointerDown(e: PointerEvent) {
		swipeStart = { x: e.clientX, y: e.clientY };
	}
	function onPointerUp(e: PointerEvent) {
		if (!swipeStart) return;
		const dx = e.clientX - swipeStart.x;
		const dy = e.clientY - swipeStart.y;
		swipeStart = null;
		if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy) * 1.5) {
			if (dx < 0) next();
			else prev();
		}
	}
</script>

<svelte:window onkeydown={onKeydown} />

<section class="deck" aria-roledescription="story deck" bind:this={deckEl}>
	<!-- svelte-ignore a11y_no_static_element_interactions -- swipe is a redundant
	     affordance; buttons/keys provide the accessible path -->
	<div class="deck-chart" onpointerdown={onPointerDown} onpointerup={onPointerUp}>
		{@render graphic()}

		<!-- edge tap zones (outer ~15%); center stays free for chart tooltips -->
		<button class="tap left" onclick={prev} aria-label={i18n.t('story.nav.prev')} tabindex="-1"
		></button>
		<button class="tap right" onclick={next} aria-label={i18n.t('story.nav.next')} tabindex="-1"
		></button>
	</div>

	<aside class="deck-copy">
		{#each steps as s, i (s.id)}
			{#if i === $activeStepIndex}
				<div class="copy-active">
					{@render step(s.id, i, true)}
				</div>
			{/if}
		{/each}
		<p class="hint" aria-hidden="true">{i18n.t('story.arrowHint')}</p>

		<!-- full copy stays in the prerendered DOM for crawlers / no-JS readers -->
		<div class="sr-only">
			{#each steps as s, i (s.id)}
				{#if i !== $activeStepIndex}
					{@render step(s.id, i, false)}
				{/if}
			{/each}
		</div>
	</aside>

	<div class="deck-controls">
		<StoryProgress />
	</div>
</section>

<style>
	.deck {
		display: grid;
		grid-template:
			'copy chart' minmax(0, 1fr)
			'controls controls' auto
			/ minmax(17rem, 23rem) minmax(0, 1fr);
		height: calc(100svh - 3.4rem); /* below the site header */
		min-height: 480px;
	}
	.deck-chart {
		grid-area: chart;
		position: relative;
		display: flex;
		flex-direction: column;
		justify-content: center;
		min-width: 0;
		min-height: 0;
		overflow: hidden; /* charts must never bleed into the progress bar */
		touch-action: pan-y;
	}
	.deck-copy {
		grid-area: copy;
		display: flex;
		flex-direction: column;
		justify-content: center;
		gap: 0.75rem;
		padding: 1rem 1.25rem;
		border-right: 1px solid var(--color-border);
		overflow-y: auto;
		min-height: 0;
	}
	.deck-controls {
		grid-area: controls;
	}
	.tap {
		position: absolute;
		top: 0;
		bottom: 0;
		width: 14%;
		border: none;
		background: transparent;
		cursor: pointer;
		padding: 0;
	}
	.tap.left {
		left: 0;
	}
	.tap.right {
		right: 0;
	}
	.tap:focus-visible {
		outline: 2px solid var(--color-ink);
		outline-offset: -4px;
	}
	.hint {
		font-size: 0.75rem;
		color: var(--color-ink-muted);
		margin: 0;
	}

	@media (max-width: 899px) {
		.deck {
			grid-template:
				'chart' minmax(0, 1.5fr)
				'copy' minmax(0, 1fr)
				'controls' auto
				/ 1fr;
		}
		.deck-copy {
			border-right: none;
			border-top: 1px solid var(--color-border);
			justify-content: flex-start;
			padding: 0.75rem 1rem;
		}
	}
</style>
