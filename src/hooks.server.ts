import type { Handle } from '@sveltejs/kit';

// Runs at prerender time: stamps the correct lang attribute into each
// prerendered HTML file (/en/* -> lang="en", /zh/* -> lang="zh").
export const handle: Handle = async ({ event, resolve }) => {
	const lang = event.params.lang ?? 'en';
	return resolve(event, {
		transformPageChunk: ({ html }) => html.replace('%app.lang%', lang)
	});
};
