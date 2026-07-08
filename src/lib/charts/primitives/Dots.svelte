<script module lang="ts">
	export interface Dot {
		id: string;
		x: number;
		y: number;
		kind: 'hot' | 'cold';
		/** has a curated story event attached */
		featured: boolean;
	}
</script>

<script lang="ts">
	// Outlier/record day dots. Hot dots sit above the band, cold below —
	// position encodes the category redundantly with color (grayscale-safe).
	// Dots with a curated event get a ring and a bigger hit target.
	let {
		x,
		y,
		dots,
		r = 3.5,
		featuredR = 6,
		onfocus,
		onblur,
		onselect
	}: {
		x: d3.ScaleLinear<number, number>;
		y: d3.ScaleLinear<number, number>;
		dots: Dot[];
		r?: number;
		featuredR?: number;
		onfocus?: (dot: Dot, px: number, py: number) => void;
		onblur?: () => void;
		onselect?: (dot: Dot, px: number, py: number) => void;
	} = $props();
</script>

<g class="dots">
	{#each dots as dot (dot.id)}
		{@const px = x(dot.x)}
		{@const py = y(dot.y)}
		{@const radius = dot.featured ? featuredR : r}
		<circle
			cx={px}
			cy={py}
			r={radius}
			class="dot {dot.kind}"
			class:featured={dot.featured}
		/>
		<!-- oversized invisible hit target; keyboard-focusable when featured -->
		<circle
			cx={px}
			cy={py}
			r={Math.max(radius + 6, 12)}
			class="hit"
			role={dot.featured ? 'button' : undefined}
			tabindex={dot.featured ? 0 : undefined}
			aria-label={dot.featured ? dot.id : undefined}
			onmouseenter={() => onfocus?.(dot, px, py)}
			onmouseleave={() => onblur?.()}
			onfocus={() => onfocus?.(dot, px, py)}
			onblur={() => onblur?.()}
			onclick={() => onselect?.(dot, px, py)}
			onkeydown={(e) => {
				if (e.key === 'Enter' || e.key === ' ') {
					e.preventDefault();
					onselect?.(dot, px, py);
				}
			}}
		/>
	{/each}
</g>

<style>
	.dot {
		stroke: var(--color-paper);
		stroke-width: 1;
		transition: r 150ms ease;
	}
	.dot.hot {
		fill: var(--color-hot);
	}
	.dot.cold {
		fill: var(--color-cold);
	}
	.dot.featured {
		stroke: var(--color-ink);
		stroke-width: 1.5;
	}
	.hit {
		fill: transparent;
		cursor: pointer;
	}
	.hit:focus-visible {
		outline: 2px solid var(--color-ink);
		outline-offset: 2px;
	}
</style>
