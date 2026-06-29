/**
 * main.js — Redarky Reddit Scraper (Apify Actor)
 */

import { Actor } from 'apify';
import { 
    fetchSubredditNew, 
    fetchByKeyword, 
    populatePostDetailsAndComments 
} from './src/reddit.js';
import { withRetry, safeRun } from './src/retry.js';
import { sendWebhook } from './src/webhook.js';

await Actor.init();

try {
    // ── 1. Read and validate input ────────────────────────────────────────────
    const input = await Actor.getInput() || {};
    const {
        subreddits = [],
        keywords = [], 
        sinceTimestamp = 0,
        postsPerSubreddit = 5,
        fetchComments = true,
        commentsPerSubreddit = 5,
        itemsPerKeyword = 10, 
        webhookUrl = '',
        projectId = '',
        sourceRunId = '',
    } = input;

    const cleanSubreddits = subreddits
        .map((s) => String(s).trim().replace(/^r\//i, ''))
        .filter((s) => s.length > 0 && /^[A-Za-z0-9_]{1,50}$/.test(s));

    const cleanKeywords = keywords
        .map((k) => String(k).trim())
        .filter((k) => k.length > 0);

    if (cleanSubreddits.length === 0 && cleanKeywords.length === 0) {
        throw new Error('Input must include at least one target subreddit or search keyword.');
    }

    const effectiveSince = sinceTimestamp > 0
        ? sinceTimestamp
        : Math.floor(Date.now() / 1000) - (35 * 60);

    console.log(`Starting run — Since ${new Date(effectiveSince * 1000).toISOString()}`);
    if (cleanSubreddits.length > 0) console.log(`Target Subreddits: ${cleanSubreddits.join(', ')}`);
    if (cleanKeywords.length > 0) console.log(`Target Keywords: ${cleanKeywords.join(', ')}`);

    // ── 2. Environment-Aware Proxy Configuration ──────────────────────────────
    const isLocal = process.env.APIFY_IS_AT_HOME !== '1';
    let proxyConfiguration = null;

    if (!isLocal) {
        console.log('[Cloud-Run] Initializing Apify Cloud Residential infrastructure.');
        proxyConfiguration = await Actor.createProxyConfiguration({
            groups: ['RESIDENTIAL'],
            countryCode: 'US',
        });
    } else {
        console.log('[Local-Test] Running outside Apify Cloud.');
    }

    const allItems = [];
    const seenExternalIds = new Set();
    const runErrors = [];
    let totalRequests = 0;
    const startTime = Date.now();

    // ── 3. Routing Matrix Resolution ──────────────────────────────────────────
    
    // MODE 1: Subreddits provided but NO keywords
    if (cleanSubreddits.length > 0 && cleanKeywords.length === 0) {
        for (const subreddit of cleanSubreddits) {
            console.log(`\n--- Scraping Subreddit Feed r/${subreddit} ---`);
            const proxyUrl = proxyConfiguration ? await proxyConfiguration.newUrl() : null;

            const { result, error } = await safeRun(
                () => withRetry(
                    () => fetchSubredditNew({
                        subreddit,
                        postsLimit: postsPerSubreddit,
                        proxyUrl,
                    }),
                    { label: `r/${subreddit}`, maxAttempts: 3, baseDelayMs: 4_000 }
                ),
                `r/${subreddit}`
            );

            if (error) {
                runErrors.push(`r/${subreddit}: ${error.message}`);
                continue;
            }

            totalRequests += 1;
            processExtractedItems(result);
        }
    } 
    
    // MODE 2: Subreddits AND Keywords provided
    else if (cleanSubreddits.length > 0 && cleanKeywords.length > 0) {
        for (const subreddit of cleanSubreddits) {
            for (const keyword of cleanKeywords) {
                console.log(`\n--- Searching Keyword: "${keyword}" inside r/${subreddit} ---`);
                const proxyUrl = proxyConfiguration ? await proxyConfiguration.newUrl() : null;

                const { result, error } = await safeRun(
                    () => withRetry(
                        () => fetchByKeyword({
                            keyword,
                            subreddit,
                            targetLimit: itemsPerKeyword,
                            proxyUrl,
                        }),
                        { label: `r/${subreddit}-${keyword}`, maxAttempts: 3, baseDelayMs: 4_000 }
                    ),
                    `r/${subreddit}-${keyword}`
                );

                if (error) {
                    runErrors.push(`r/${subreddit} keyword "${keyword}": ${error.message}`);
                    continue;
                }

                totalRequests += 1;
                processExtractedItems(result);
            }
        }
    } 
    
    // MODE 3: NO Subreddits provided but Keywords exist
    else if (cleanSubreddits.length === 0 && cleanKeywords.length > 0) {
        for (const keyword of cleanKeywords) {
            console.log(`\n--- Searching Global Keyword: "${keyword}" ---`);
            const proxyUrl = proxyConfiguration ? await proxyConfiguration.newUrl() : null;

            const { result, error } = await safeRun(
                () => withRetry(
                    () => fetchByKeyword({
                        keyword,
                        subreddit: null,
                        targetLimit: itemsPerKeyword,
                        proxyUrl,
                    }),
                    { label: `global-keyword: ${keyword}`, maxAttempts: 3, baseDelayMs: 4_000 }
                ),
                `global-keyword: ${keyword}`
            );

            if (error) {
                runErrors.push(`global keyword "${keyword}": ${error.message}`);
                continue;
            }

            totalRequests += 1;
            processExtractedItems(result);
        }
    }

    function processExtractedItems(items) {
        let newItemsCount = 0;
        for (const item of items) {
            const key = `${item.source}:${item.external_id}:${item.post_type}`;
            if (seenExternalIds.has(key)) continue;
            seenExternalIds.add(key);
            allItems.push(item);
            newItemsCount++;
        }
        console.log(`Added ${newItemsCount} new elements to run context payload.`);
    }

    // ── 4. Step C: Deep-Dive Secondary Thread Parsing (Optimized Parallel Execution) ──
    // ── 4. Step C: Deep-Dive Secondary Thread Parsing (Optimized Parallel Execution) ──
    if (fetchComments && allItems.length > 0) {
        console.log(`\n--- Deep parsing details for ${allItems.length} items ---`);
        
        // FIX: Always hydrate if it has comments OR if it came from a search result card (missing content body)
        const itemsNeedingHydration = allItems.filter(item => item.comments_count > 0 || !item.content || item.matched_keyword !== null);
        console.log(`Auto-skipping ${allItems.length - itemsNeedingHydration.length} entries with verified 0 comments/content.`);

        // Process across standard concurrent batch windows (Safe anti-throttling width)
        const CONCURRENCY_LIMIT = 3;
        for (let i = 0; i < itemsNeedingHydration.length; i += CONCURRENCY_LIMIT) {
            const chunk = itemsNeedingHydration.slice(i, i + CONCURRENCY_LIMIT);
            
            await Promise.all(chunk.map(async (item) => {
                const proxyUrl = proxyConfiguration ? await proxyConfiguration.newUrl() : null;
                console.log(` -> Parallel fetching details: ${item.url}`);

                const { result, error } = await safeRun(
                    () => withRetry(
                        () => populatePostDetailsAndComments({
                            item,
                            commentsLimit: commentsPerSubreddit,
                            proxyUrl,
                        }),
                        { label: `details: ${item.url}`, maxAttempts: 2, baseDelayMs: 2_000 }
                    ),
                    `details: ${item.url}`
                );

                if (!error && result) {
                    totalRequests += 1;
                    Object.assign(item, result); 
                } else if (error) {
                    runErrors.push(`details frame parsing failed for ${item.url}: ${error.message}`);
                }
            }));
        }
    }

    // ── 5. Run Summary Calculations ──────────────────────────────────────────
    const durationMs = Date.now() - startTime;
    const postCount = allItems.filter((i) => i.post_type === 'post').length;
    let commentCount = 0;
    allItems.forEach(item => {
        if (item.comments && Array.isArray(item.comments)) {
            commentCount += item.comments.length;
        }
    });

    console.log(`\n=== Run complete ===`);
    console.log(`Total main posts collected: ${allItems.length} (${postCount} posts, ${commentCount} aggregated comments inline)`);
    console.log(`Total Browser Crawl Requests: ${totalRequests}`);
    console.log(`Duration: ${(durationMs / 1000).toFixed(1)}s`);
    if (runErrors.length > 0) {
        console.warn(`Errors encountered (${runErrors.length}): ${runErrors.join('; ')}`);
    }

    // ── 6. Write to Apify Dataset Storage ─────────────────────────────────────
    if (allItems.length > 0) {
        await Actor.pushData(allItems);
        console.log(`Pushed data payload directly into active Apify dataset.`);
    }

    // ── 7. Send Structured Delivery Payload to Webhook ────────────────────────
    const stats = {
        total_items: allItems.length,
        posts: postCount,
        comments: commentCount,
        request_count: totalRequests,
        duration_ms: durationMs,
        errors: runErrors,
    };

    if (webhookUrl) {
        const webhookPayload = {
            source_run_id: sourceRunId || Actor.getEnv().actorRunId,
            project_id: projectId,
            subreddits: cleanSubreddits,
            keywords: cleanKeywords,
            items: allItems,
            stats,
        };

        const delivered = await sendWebhook(webhookUrl, webhookPayload);
        if (!delivered) console.warn('[webhook] Outbound delivery failed.');
    } else {
        console.log('No webhookUrl set — local storage tracking data matching finalized.');
    }

    await Actor.setValue('RUN_STATS', stats);

} catch (err) {
    console.error(`Fatal error inside runtime thread: ${err.message}`);
    await Actor.fail(err.message);
} finally {
    await Actor.exit();
}