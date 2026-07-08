// Central reduced-motion check. Read once; used to zero out tween durations.

import { browser } from '$app/environment';

export const prefersReducedMotion: boolean = browser
	? window.matchMedia('(prefers-reduced-motion: reduce)').matches
	: false;

/** Tween duration honoring the user's motion preference. */
export const motionDuration = (ms: number) => (prefersReducedMotion ? 0 : ms);
