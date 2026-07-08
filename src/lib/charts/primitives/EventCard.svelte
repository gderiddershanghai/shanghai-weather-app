<script lang="ts">
	// Bilingual story card for a curated event: date, temps, note, news links,
	// OG thumbnail. Floating card on desktop; bottom sheet on small screens.
	import { eventImageUrl, type CuratedEvent } from '$lib/data/load';
	import { getI18n } from '$lib/i18n';
	import { formatDate, formatTemp } from '$lib/utils/format';

	let {
		event,
		onclose
	}: {
		event: CuratedEvent;
		onclose?: () => void;
	} = $props();

	const i18n = getI18n();

	const note = $derived(event.note[i18n.lang] ?? event.note.en);
	const imgSrc = $derived(eventImageUrl(event.image));
	// show links for BOTH languages when available — a zh reader may want the
	// English source and vice versa
	const links = $derived(
		(['en', 'zh'] as const)
			.map((l) => ({ lang: l, link: event.links[l] }))
			.filter((e) => e.link?.url)
	);
	const spansDays = $derived(event.days > 1);
</script>

<aside class="event-card" role="dialog" aria-label={note ?? event.id}>
	<button class="close" onclick={() => onclose?.()} aria-label="close">×</button>

	{#if imgSrc}
		<img src={imgSrc} alt="" loading="lazy" />
	{/if}

	<div class="body">
		<p class="date">
			{formatDate(event.date, i18n.lang)}
			{#if spansDays}
				<span class="duration">
					({event.days}{i18n.lang === 'zh' ? '天' : ' days'})
				</span>
			{/if}
		</p>

		{#if note}
			<p class="note">{note}</p>
		{/if}

		<p class="temps">
			{#if event.real_c != null}
				<span class="temp {event.category === 'COLD' ? 'cold' : 'hot'}">
					{formatTemp(event.real_c)}
				</span>
			{/if}
			{#if event.feels_c != null}
				<span class="feels">
					{i18n.lang === 'zh' ? '体感' : 'feels like'}
					{formatTemp(event.feels_c)}
				</span>
			{/if}
		</p>

		{#if links.length}
			<ul class="links">
				{#each links as { lang, link } (lang)}
					<li>
						<a href={link!.url} target="_blank" rel="noopener noreferrer" lang={lang === 'zh' ? 'zh' : 'en'}>
							{link!.outlet ?? new URL(link!.url!).hostname}
							{#if link!.headline}
								<span class="headline">— {link!.headline}</span>
							{/if}
						</a>
					</li>
				{/each}
			</ul>
		{/if}
	</div>
</aside>

<style>
	.event-card {
		position: absolute;
		z-index: 20;
		width: min(320px, 90vw);
		background: var(--color-paper);
		border: 1px solid var(--color-border);
		border-radius: 8px;
		box-shadow: 0 8px 24px rgb(0 0 0 / 0.12);
		overflow: hidden;
	}
	.close {
		position: absolute;
		top: 4px;
		right: 4px;
		border: none;
		background: var(--color-paper);
		border-radius: 50%;
		width: 1.6rem;
		height: 1.6rem;
		font-size: 1rem;
		line-height: 1;
		cursor: pointer;
		z-index: 1;
	}
	img {
		width: 100%;
		aspect-ratio: 16 / 9;
		object-fit: cover;
		display: block;
	}
	.body {
		padding: 0.75rem;
		display: grid;
		gap: 0.35rem;
	}
	.date {
		margin: 0;
		font-weight: 700;
		font-size: 0.9rem;
	}
	.duration {
		font-weight: 400;
		color: var(--color-ink-muted);
	}
	.note {
		margin: 0;
		font-size: 0.9rem;
	}
	.temps {
		margin: 0;
		font-size: 0.9rem;
		display: flex;
		gap: 0.6rem;
		font-variant-numeric: tabular-nums;
	}
	.temp.hot {
		color: var(--color-hot);
		font-weight: 700;
	}
	.temp.cold {
		color: var(--color-cold);
		font-weight: 700;
	}
	.feels {
		color: var(--color-ink-muted);
	}
	.links {
		margin: 0.2rem 0 0;
		padding: 0;
		list-style: none;
		font-size: 0.8rem;
		display: grid;
		gap: 0.25rem;
	}
	.links a {
		color: var(--color-ink-muted);
	}
	.headline {
		font-style: italic;
	}

	@media (max-width: 640px) {
		.event-card {
			position: fixed;
			left: 0.5rem;
			right: 0.5rem;
			bottom: 0.5rem;
			width: auto;
		}
	}
</style>
