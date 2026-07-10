<script lang="ts">
	// Bilingual story card for a curated event. Every card is the SAME size:
	// fixed media area (image or category-tinted placeholder), date row,
	// note clamped to 4 lines, and a "Read more" footer pinned to the bottom.
	// Shown as a hover preview first; a click pins it (parent controls that).
	import { eventImageUrl, type CuratedEvent } from '$lib/data/load';
	import { getI18n } from '$lib/i18n';
	import { formatDate, formatTemp } from '$lib/utils/format';

	let {
		event,
		pinned = true,
		onclose
	}: {
		event: CuratedEvent;
		/** false = hover preview (no close button, shows pin hint) */
		pinned?: boolean;
		onclose?: () => void;
	} = $props();

	const i18n = getI18n();

	const note = $derived(event.note[i18n.lang] ?? event.note.en);
	const imgSrc = $derived(eventImageUrl(event.image));

	// one primary "Read more" in the reader's language; the other language
	// (when available) gets a small secondary chip so nothing is lost
	const otherLang = $derived(i18n.lang === 'zh' ? 'en' : 'zh');
	const primary = $derived(
		event.links[i18n.lang]?.url ? event.links[i18n.lang] : event.links[otherLang]
	);
	const secondary = $derived(
		primary === event.links[i18n.lang] && event.links[otherLang]?.url
			? event.links[otherLang]
			: null
	);
	const spansDays = $derived(event.days > 1);

	function onkeydown(e: KeyboardEvent) {
		if (e.key === 'Escape' && pinned) onclose?.();
	}
</script>

<svelte:window {onkeydown} />

<div class="event-card" class:preview={!pinned} role="dialog" aria-label={note ?? event.id}>
	{#if pinned}
		<button class="close" onclick={() => onclose?.()} aria-label={i18n.t('event.close')}>×</button>
	{/if}

	<div class="media cat-{event.category.toLowerCase()}">
		{#if imgSrc}
			<img src={imgSrc} alt="" loading="lazy" />
		{:else}
			<span class="media-year">{event.year}</span>
		{/if}
	</div>

	<div class="body">
		<p class="date">
			{formatDate(event.date, i18n.lang)}
			{#if spansDays}
				<span class="duration">
					({event.days}{i18n.lang === 'zh' ? '天' : ' days'})
				</span>
			{/if}
			{#if event.real_c != null}
				<span class="temp {event.category === 'COLD' ? 'cold' : 'hot'}">
					{formatTemp(event.real_c)}
				</span>
			{/if}
			{#if event.feels_c != null}
				<span class="feels">
					{i18n.lang === 'zh' ? '体感' : 'feels'}
					{formatTemp(event.feels_c)}
				</span>
			{/if}
		</p>

		{#if note}
			<p class="note">{note}</p>
		{/if}

		<p class="footer">
			{#if primary?.url}
				<a class="read-more" href={primary.url} target="_blank" rel="noopener noreferrer">
					{i18n.t('event.readMore')}
					{#if primary.outlet}<span class="outlet">· {primary.outlet}</span>{/if}
					<span aria-hidden="true">→</span>
				</a>
				{#if secondary?.url}
					<a
						class="alt-lang"
						href={secondary.url}
						target="_blank"
						rel="noopener noreferrer"
						lang={otherLang}
					>
						{otherLang === 'zh' ? '中文' : 'EN'}
					</a>
				{/if}
			{:else if !pinned}
				<span class="pin-hint">{i18n.t('event.pinHint')}</span>
			{/if}
		</p>
	</div>
</div>

<style>
	.event-card {
		position: absolute;
		z-index: 20;
		display: flex;
		flex-direction: column;
		/* every card the same box — media + body heights are fixed */
		width: min(300px, 88vw);
		height: 302px;
		background: var(--color-paper);
		border: 1px solid var(--color-border);
		border-radius: 8px;
		box-shadow: 0 8px 24px rgb(0 0 0 / 0.12);
		overflow: hidden;
	}
	.event-card.preview {
		pointer-events: auto;
		box-shadow: 0 4px 14px rgb(0 0 0 / 0.1);
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
	.media {
		height: 132px;
		flex: 0 0 132px;
		display: grid;
		place-items: center;
	}
	.media img {
		width: 100%;
		height: 100%;
		object-fit: cover;
		display: block;
	}
	/* no-image fallback: category-tinted block so the box never collapses */
	.media-year {
		font-size: 2.4rem;
		font-weight: 700;
		color: var(--color-paper);
		opacity: 0.85;
		font-variant-numeric: tabular-nums;
	}
	.media.cat-hot {
		background: var(--chapter-heat);
	}
	.media.cat-cold {
		background: var(--chapter-cold);
	}
	.media.cat-rain,
	.media.cat-typhoon {
		background: var(--chapter-rain);
	}
	.media.cat-aqi {
		background: var(--chapter-aqi);
	}

	.body {
		flex: 1;
		min-height: 0;
		display: flex;
		flex-direction: column;
		gap: 0.35rem;
		padding: 0.7rem 0.75rem 0.6rem;
	}
	.date {
		margin: 0;
		font-weight: 700;
		font-size: 0.88rem;
		display: flex;
		flex-wrap: wrap;
		align-items: baseline;
		gap: 0.45rem;
		font-variant-numeric: tabular-nums;
	}
	.duration {
		font-weight: 400;
		color: var(--color-ink-muted);
	}
	.temp.hot {
		color: var(--color-hot);
	}
	.temp.cold {
		color: var(--color-cold);
	}
	.feels {
		font-weight: 400;
		color: var(--color-ink-muted);
	}
	.note {
		margin: 0;
		font-size: 0.85rem;
		line-height: 1.35;
		display: -webkit-box;
		-webkit-box-orient: vertical;
		-webkit-line-clamp: 4;
		line-clamp: 4;
		overflow: hidden;
	}
	.footer {
		margin: auto 0 0;
		padding-top: 0.3rem;
		font-size: 0.8rem;
		display: flex;
		align-items: baseline;
		gap: 0.6rem;
	}
	.read-more {
		font-weight: 700;
		color: var(--color-ink);
		text-decoration: none;
	}
	.read-more:hover {
		text-decoration: underline;
	}
	.outlet {
		font-weight: 400;
		color: var(--color-ink-muted);
	}
	.alt-lang {
		color: var(--color-ink-muted);
		font-size: 0.75rem;
	}
	.pin-hint {
		color: var(--color-ink-muted);
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
