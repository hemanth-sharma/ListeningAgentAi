/**
 * src/webhook.js
 *
 * Delivers scraped items to the Redarky FastAPI backend via HTTP POST.
 *
 * Why POST instead of relying only on the Apify dataset?
 *   - The dataset is fine for debugging, but pulling it from Python requires
 *     a polling loop or a separate Apify API call after the run finishes.
 *   - A direct webhook POST lets the backend start processing immediately
 *     when the actor finishes, with no polling delay.
 *   - The actor bundles results in one payload so the backend makes one DB
 *     write call rather than paginating through an Apify dataset.
 *
 * The actor still writes to the Apify dataset (Actor.pushData) as a backup.
 * The webhook is the fast path; the dataset is the debug/replay path.
 */

import { gotScraping } from 'got-scraping';

/**
 * sendWebhook — POSTs the scrape results to the backend ingestion endpoint.
 *
 * The backend expects:
 * {
 *   source_run_id: string,   // for correlating to monitored_sources row
 *   project_id: string,      // which Redarky project this run was for
 *   subreddits: string[],    // which subreddits were scraped
 *   items: ScrapedItem[],    // the normalised posts and comments
 *   stats: {
 *     total_items: number,
 *     posts: number,
 *     comments: number,
 *     request_count: number,
 *     duration_ms: number,
 *     errors: string[],
 *   }
 * }
 *
 * @param {string} webhookUrl
 * @param {object} payload
 * @returns {boolean} true on success
 */
export async function sendWebhook(webhookUrl, payload) {
    if (!webhookUrl) return false;

    try {
        const response = await gotScraping.post(webhookUrl, {
            json: payload,
            timeout: { request: 20_000 },
            throwHttpErrors: false,  // handle manually so we can log the body
        });

        if (response.statusCode >= 200 && response.statusCode < 300) {
            console.log(`[webhook] Delivered ${payload.items.length} items → ${webhookUrl} (${response.statusCode})`);
            return true;
        } else {
            console.error(`[webhook] Non-2xx response: ${response.statusCode} — ${response.body?.slice(0, 200)}`);
            return false;
        }
    } catch (err) {
        console.error(`[webhook] Delivery failed: ${err.message}`);
        return false;
    }
}