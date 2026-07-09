<script lang="ts">
	// Pudding-style progress: one dash per step (clickable), chapter + counter,
	// prev/next buttons, and an aria-live announcer for step changes.
	import { activeStepIndex, goTo, next, prev } from '$lib/stores/story';
	import { steps } from './steps';
	import { getI18n } from '$lib/i18n';

	const i18n = getI18n();

	const current = $derived(steps[$activeStepIndex]);
</script>

<nav class="progress" aria-label={i18n.t('story.progressLabel')}>
	<button class="arrow" onclick={prev} disabled={$activeStepIndex === 0} aria-label={i18n.t('story.nav.prev')}>
		‹
	</button>

	<div class="dashes" role="group">
		{#each steps as s, i (s.id)}
			<button
				class="dash chapter-{s.chapter}"
				class:done={i < $activeStepIndex}
				class:current={i === $activeStepIndex}
				onclick={() => goTo(i)}
				aria-label="{i18n.t(`story.chapter.${s.chapter}`)} {i + 1}/{steps.length}"
				aria-current={i === $activeStepIndex ? 'step' : undefined}
			></button>
		{/each}
	</div>

	<span class="counter">
		{i18n.t(`story.chapter.${current.chapter}`)} · {$activeStepIndex + 1}/{steps.length}
	</span>

	<button
		class="arrow"
		onclick={next}
		disabled={$activeStepIndex === steps.length - 1}
		aria-label={i18n.t('story.nav.next')}
	>
		›
	</button>

	<span class="sr-only" aria-live="polite">{i18n.t(`steps.${current.id}.title`)}</span>
</nav>

<style>
	.progress {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 0.5rem 1rem;
		border-top: 1px solid var(--color-border);
		background: var(--color-paper);
	}
	.arrow {
		font: inherit;
		font-size: 1.4rem;
		line-height: 1;
		width: 2.2rem;
		height: 2.2rem;
		border: 1px solid var(--color-border);
		border-radius: 50%;
		background: var(--color-paper);
		cursor: pointer;
		flex-shrink: 0;
	}
	.arrow:disabled {
		opacity: 0.3;
		cursor: default;
	}
	.dashes {
		display: flex;
		gap: 3px;
		flex: 1;
		min-width: 0;
	}
	.dash {
		flex: 1;
		height: 6px;
		border: none;
		border-radius: 3px;
		background: var(--color-border);
		cursor: pointer;
		padding: 0;
		min-width: 8px;
	}
	.dash.done {
		background: var(--color-ink-muted);
	}
	.dash.current {
		background: var(--color-ink);
	}
	.counter {
		font-size: 0.75rem;
		color: var(--color-ink-muted);
		white-space: nowrap;
		font-variant-numeric: tabular-nums;
	}
	@media (max-width: 640px) {
		.counter {
			display: none;
		}
	}
</style>
