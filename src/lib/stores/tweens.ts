// Tweened shadows of the numeric chart-state fields. Charts read these for
// their scales so domain changes animate; discrete flags cross-fade via CSS.
// Uses the Svelte 5 `Tween` class (svelte/motion) — not the deprecated `tweened`.

import { cubicInOut } from 'svelte/easing';
import { Tween } from 'svelte/motion';
import { derived, type Readable } from 'svelte/store';
import { chartState, CHART_DEFAULTS } from './chartState';
import { motionDuration } from '$lib/utils/motion';

const DURATION = motionDuration(800);

const xDomainTween = new Tween<[number, number]>(CHART_DEFAULTS.xDomain, {
	duration: DURATION,
	easing: cubicInOut
});

// yDomain can be null (auto); tween only when both ends are numeric.
const yDomainTween = new Tween<[number, number]>([0, 1], {
	duration: DURATION,
	easing: cubicInOut
});
let yIsAuto = true;

chartState.subscribe((s) => {
	xDomainTween.target = s.xDomain;
	if (s.yDomain) {
		if (yIsAuto) {
			// jumping from auto: snap, don't tween from a stale domain
			yDomainTween.set(s.yDomain, { duration: 0 });
		} else {
			yDomainTween.target = s.yDomain;
		}
		yIsAuto = false;
	} else {
		yIsAuto = true;
	}
});

/**
 * Readable view of the tweened domains. Charts subscribe to this for scales.
 * `yDomain` is null while in auto mode — charts then fit to data themselves.
 */
export const tweenedDomains: Readable<{
	xDomain: [number, number];
	yDomain: [number, number] | null;
}> = derived(chartState, (s, set) => {
	let frame = 0;
	const tick = () => {
		set({
			xDomain: xDomainTween.current,
			yDomain: s.yDomain ? yDomainTween.current : null
		});
		if (
			xDomainTween.current !== xDomainTween.target ||
			(s.yDomain && yDomainTween.current !== yDomainTween.target)
		) {
			frame = requestAnimationFrame(tick);
		}
	};
	tick();
	return () => cancelAnimationFrame(frame);
});
