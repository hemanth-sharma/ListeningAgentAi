/**
 * src/retry.js
 *
 * Exponential backoff retry wrapper.
 *
 * Reddit returns 429 (rate limit) when we hit too fast, and occasionally
 * 503 during traffic spikes. We retry with backoff rather than failing the
 * whole run. After maxAttempts failures on one subreddit, we log the error
 * and continue with the next — one bad subreddit shouldn't kill the run.
 */

/**
 * withRetry — wraps an async function with exponential backoff.
 *
 * @param {() => Promise<T>} fn - the async operation to retry
 * @param {object} opts
 * @param {number} opts.maxAttempts - total attempts before giving up (default 4)
 * @param {number} opts.baseDelayMs - first retry delay in ms (default 2000)
 * @param {number} opts.maxDelayMs  - cap on delay (default 30000)
 * @param {string} opts.label       - logged with each retry for debugging
 * @returns {Promise<T>}
 * @throws the last error if all attempts exhausted
 */
export async function withRetry(fn, {
    maxAttempts = 4,
    baseDelayMs = 2_000,
    maxDelayMs = 30_000,
    label = 'operation',
} = {}) {
    let lastError;

    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
        try {
            return await fn();
        } catch (err) {
            lastError = err;

            const isRateLimit = err.response?.statusCode === 429;
            const isServerError = err.response?.statusCode >= 500;
            const isNetworkError = !err.response; // timeout, ECONNRESET, etc.

            // Only retry on transient errors
            if (!isRateLimit && !isServerError && !isNetworkError) {
                throw err; // 4xx (except 429) — not worth retrying
            }

            if (attempt === maxAttempts) break;

            // Exponential backoff with jitter: delay = base * 2^attempt + random(0, 500ms)
            const exponentialDelay = baseDelayMs * Math.pow(2, attempt - 1);
            const jitter = Math.floor(Math.random() * 500);
            const delay = Math.min(exponentialDelay + jitter, maxDelayMs);

            const reason = isRateLimit ? '429 rate-limited' : isServerError ? `${err.response?.statusCode} server error` : 'network error';
            console.warn(`[retry] ${label} — attempt ${attempt}/${maxAttempts} failed (${reason}). Waiting ${delay}ms...`);

            await new Promise((resolve) => setTimeout(resolve, delay));
        }
    }

    throw lastError;
}

/**
 * safeRun — runs an async function and returns { result, error } instead of
 * throwing. Lets the main loop continue after a subreddit fails.
 *
 * @param {() => Promise<T>} fn
 * @param {string} label - for logging
 * @returns {{ result: T|null, error: Error|null }}
 */
export async function safeRun(fn, label = '') {
    try {
        const result = await fn();
        return { result, error: null };
    } catch (err) {
        console.error(`[safeRun] ${label} failed: ${err.message}`);
        return { result: null, error: err };
    }
}