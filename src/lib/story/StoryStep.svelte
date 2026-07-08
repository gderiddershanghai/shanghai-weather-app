<script lang="ts">
	// One story step's copy card. Title + body come from copy.json via the
	// step's copyKey ("steps.<id>" -> "steps.<id>.title" / ".body").
	import { getI18n } from '$lib/i18n';

	let {
		copyKey,
		active = false
	}: {
		copyKey: string;
		active?: boolean;
	} = $props();

	const i18n = getI18n();

	const title = $derived(i18n.t(`${copyKey}.title`));
	const body = $derived(i18n.t(`${copyKey}.body`));
	const hasTitle = $derived(title !== `${copyKey}.title`);
</script>

<div class="card" class:active>
	{#if hasTitle}
		<h3>{title}</h3>
	{/if}
	<p>{body}</p>
</div>

<style>
	.card {
		background: color-mix(in srgb, var(--color-paper) 92%, transparent);
		backdrop-filter: blur(2px);
		border: 1px solid var(--color-border);
		border-radius: 8px;
		padding: 1rem 1.25rem;
		box-shadow: 0 2px 12px rgb(0 0 0 / 0.06);
		opacity: 0.55;
		transition: opacity 250ms ease;
	}
	.card.active {
		opacity: 1;
	}
	h3 {
		margin: 0 0 0.5rem;
		font-size: 1.05rem;
	}
	p {
		margin: 0;
		font-size: 0.95rem;
	}
</style>
