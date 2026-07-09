// Story navigation state: arrow/tap-driven step deck.
// The index store is the driver; goTo() applies chart presets. Because step
// presets are PARTIAL (unspecified keys carry over from the previous step),
// non-adjacent jumps replay-fold presets 0..target so the chart never lands
// in a half-configured state.

import { derived, get, writable } from 'svelte/store';
import { browser } from '$app/environment';
import { applyPreset, CHART_DEFAULTS, type ChartState } from './chartState';
import { steps } from '$lib/story/steps';

export const activeStepIndex = writable(0);
export const activeStepId = derived(activeStepIndex, (i) => steps[i]?.id ?? null);

function stepPreset(i: number): Partial<ChartState> {
	const s = steps[i];
	return {
		...s.chart,
		activeAnnotations: s.annotations ?? [],
		focusedEventId: s.focusEvent ?? null
	};
}

/** Fold presets 0..index — the complete state a linear reader would have. */
function foldedPreset(index: number): Partial<ChartState> {
	let acc: Partial<ChartState> = {};
	for (let i = 0; i <= index; i++) acc = { ...acc, ...stepPreset(i) };
	return acc;
}

export function goTo(index: number): void {
	const target = Math.max(0, Math.min(steps.length - 1, index));
	const from = get(activeStepIndex);
	activeStepIndex.set(target);

	if (Math.abs(target - from) <= 1) {
		applyPreset(stepPreset(target));
	} else {
		// jump: rebuild from defaults + folded presets
		applyPreset({ ...CHART_DEFAULTS, ...foldedPreset(target) });
	}

	if (browser) {
		// replaceState (not pushState): back button leaves the story, and old
		// WeChat webviews mishandle pushState spam
		const hash = target === 0 ? ' ' : `#${steps[target].id}`;
		history.replaceState(null, '', hash === ' ' ? location.pathname : hash);
	}
}

export const next = (): void => goTo(get(activeStepIndex) + 1);
export const prev = (): void => goTo(get(activeStepIndex) - 1);

/** Restore position from #step-id (deep link / reload); snap, don't animate. */
export function restoreFromHash(): void {
	if (!browser) return;
	const id = location.hash.slice(1);
	const index = steps.findIndex((s) => s.id === id);
	if (index > 0) {
		activeStepIndex.set(index);
		applyPreset({ ...CHART_DEFAULTS, ...foldedPreset(index) });
	} else {
		activeStepIndex.set(0);
		applyPreset(stepPreset(0));
	}
}
