<script lang="ts">
	import { onMount } from 'svelte';

	// Language redirect must use RELATIVE urls so the GitHub Pages base path is preserved.
	onMount(() => {
		const zh = navigator.languages?.some((l) => l.toLowerCase().startsWith('zh'));
		location.replace(zh ? 'zh/' : 'en/');
	});
</script>

<svelte:head>
	<title>Shanghai Weather Stories · 上海天气故事</title>
	<noscript><meta http-equiv="refresh" content="0;url=en/" /></noscript>
</svelte:head>

<main class="redirect">
	<h1>Shanghai Weather Stories<br />上海天气故事</h1>
	<p>
		<a href="en/">Continue in English</a>
		<span aria-hidden="true">·</span>
		<a href="zh/">继续使用中文</a>
	</p>
</main>

<style>
	.redirect {
		min-height: 100svh;
		display: grid;
		place-content: center;
		text-align: center;
		gap: 1rem;
	}
</style>
