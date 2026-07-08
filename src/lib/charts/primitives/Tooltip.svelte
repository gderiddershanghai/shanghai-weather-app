<script lang="ts">
	// Lightweight hover tooltip positioned inside the chart frame.
	import type { Snippet } from 'svelte';

	let {
		px,
		py,
		frameWidth,
		children
	}: {
		px: number;
		py: number;
		frameWidth: number;
		children: Snippet;
	} = $props();

	// flip to the left half when close to the right edge
	const flip = $derived(px > frameWidth * 0.65);
</script>

<div
	class="tooltip"
	style:left="{px}px"
	style:top="{py}px"
	style:transform="translate({flip ? 'calc(-100% - 12px)' : '12px'}, -50%)"
	role="status"
>
	{@render children()}
</div>

<style>
	.tooltip {
		position: absolute;
		pointer-events: none;
		background: var(--color-ink);
		color: var(--color-paper);
		padding: 0.4rem 0.6rem;
		border-radius: 4px;
		font-size: 0.8rem;
		line-height: 1.4;
		white-space: nowrap;
		z-index: 10;
	}
</style>
