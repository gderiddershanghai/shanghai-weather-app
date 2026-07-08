// Story-mode scroll state: which step is active. A single subscriber in the
// story page resolves the step definition and applies its chart preset.

import { writable } from 'svelte/store';

export const activeStepId = writable<string | null>(null);
