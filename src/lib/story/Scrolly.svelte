<script lang="ts">
	// Scroll-driven step activation. IntersectionObserver with a viewport-middle
	// activation band; falls back to a passive scroll listener on very old
	// webviews (WeChat X5). Renders a sticky graphic behind/beside the steps.
	import { onMount, type Snippet } from 'svelte';
	import { activeStepId } from '$lib/stores/story';

	let {
		stepIds,
		graphic,
		step
	}: {
		stepIds: string[];
		graphic: Snippet;
		/** renders one step's copy; receives (id, index) */
		step: Snippet<[string, number]>;
	} = $props();

	let stepEls: (HTMLElement | null)[] = $state([]);

	onMount(() => {
		const els = stepEls.filter((el): el is HTMLElement => el != null);

		if (typeof IntersectionObserver !== 'undefined') {
			const observer = new IntersectionObserver(
				(entries) => {
					for (const entry of entries) {
						if (entry.isIntersecting) {
							activeStepId.set((entry.target as HTMLElement).dataset.stepId ?? null);
						}
					}
				},
				// activation band: middle 10% of the viewport
				{ rootMargin: '-45% 0px -45% 0px', threshold: 0 }
			);
			els.forEach((el) => observer.observe(el));
			return () => observer.disconnect();
		}

		// fallback: passive scroll listener
		let ticking = false;
		const check = () => {
			ticking = false;
			const mid = window.innerHeight / 2;
			for (const el of els) {
				const rect = el.getBoundingClientRect();
				if (rect.top <= mid && rect.bottom >= mid) {
					activeStepId.set(el.dataset.stepId ?? null);
					break;
				}
			}
		};
		const onScroll = () => {
			if (!ticking) {
				ticking = true;
				requestAnimationFrame(check);
			}
		};
		window.addEventListener('scroll', onScroll, { passive: true });
		check();
		return () => window.removeEventListener('scroll', onScroll);
	});
</script>

<section class="scrolly">
	<div class="graphic">
		{@render graphic()}
	</div>
	<div class="steps">
		{#each stepIds as id, i (id)}
			<div
				class="step"
				data-step-id={id}
				bind:this={stepEls[i]}
				class:active={$activeStepId === id}
			>
				{@render step(id, i)}
			</div>
		{/each}
	</div>
</section>

<style>
	.scrolly {
		position: relative;
	}
	.graphic {
		position: sticky;
		top: 0;
		height: 100vh;
		height: 100svh;
		display: flex;
		flex-direction: column;
		justify-content: center;
		z-index: 0;
	}
	.steps {
		position: relative;
		z-index: 1;
		/* pull steps up over the sticky graphic */
		margin-top: -100vh;
		margin-top: -100svh;
		pointer-events: none;
	}
	.step {
		min-height: 90svh;
		display: flex;
		align-items: center;
		padding: 1rem;
	}
	.step > :global(*) {
		pointer-events: auto;
	}

	/* desktop: copy column on the left, chart breathing room on the right */
	@media (min-width: 900px) {
		.step {
			max-width: 22rem;
			margin-left: 4vw;
		}
	}
</style>
