/**
 * src/reddit.js
 *
 * Implements targeted subreddit parsing, cross-filtering, 
 * accurate search selectors, and single-post comment extraction.
 */

import { Actor } from 'apify';
import { PlaywrightCrawler } from '@crawlee/playwright';

// Helper function to attach network blocker rules to a page
async function applyNetworkBlocker(page) {
    await page.route('**/*', (route) => {
        const type = route.request().resourceType();
        if (['image', 'stylesheet', 'font', 'media', 'imageset'].includes(type)) {
            return route.abort();
        }
        return route.continue();
    });
}

/**
 * Mode 1: Fetch the newest un-filtered posts from a specific subreddit
 */
export async function fetchSubredditNew({ subreddit, postsLimit, proxyUrl }) {
    const fetchedAt = new Date().toISOString();
    const allItems = [];

    const crawler = new PlaywrightCrawler({
        maxRequestsPerCrawl: 1,
        headless: true,
        proxyConfiguration: proxyUrl ? await Actor.createProxyConfiguration({ proxyUrls: [proxyUrl] }) : undefined,
        async requestHandler({ page, log }) {
            await applyNetworkBlocker(page);
            log.info(`[Subreddit New] Navigating to r/${subreddit}/new/...`);
            
            await page.goto(`https://www.reddit.com/r/${subreddit}/new/`, { waitUntil: 'domcontentloaded' });
            await page.waitForSelector('shreddit-post', { timeout: 10000 }).catch(() => {});

            const extracted = await page.evaluate(() => {
                return Array.from(document.querySelectorAll('shreddit-post')).map(el => ({
                    id: el.getAttribute('id') || '',
                    title: el.getAttribute('post-title') || '',
                    author: el.getAttribute('author') || '',
                    score: parseInt(el.getAttribute('score') || '0', 10),
                    comments_count: parseInt(el.getAttribute('comment-count') || '0', 10),
                    permalink: el.getAttribute('permalink') || '',
                    content: el.querySelector('[id*="-post-rtjson-content"]')?.textContent?.trim() || ''
                }));
            });

            for (const p of extracted.slice(0, postsLimit)) {
                allItems.push({
                    source: 'reddit',
                    external_id: p.id,
                    title: p.title,
                    content: p.content,
                    author: p.author,
                    url: `https://www.reddit.com${p.permalink}`,
                    score: p.score,
                    comments_count: p.comments_count,
                    post_type: 'post',
                    subreddit: subreddit,
                    matched_keyword: null,
                    created_at_platform: Math.floor(Date.now() / 1000),
                    fetched_at: fetchedAt,
                    comments: []
                });
            }
        }
    });

    await crawler.run([`https://www.reddit.com/r/${subreddit}/new/`]);
    return allItems;
}

/**
 * Mode 2 & 3: Run targeted keyword search loops (Scoped or Global)
 */
export async function fetchByKeyword({ keyword, subreddit = null, targetLimit, proxyUrl }) {
    const fetchedAt = new Date().toISOString();
    const allItems = [];
    
    const searchUrl = subreddit 
        ? `https://www.reddit.com/r/${subreddit}/search/?q=${encodeURIComponent(keyword)}&sort=new`
        : `https://www.reddit.com/search/?q=${encodeURIComponent(keyword)}&sort=new`;

    const crawler = new PlaywrightCrawler({
        maxRequestsPerCrawl: 1,
        headless: true,
        proxyConfiguration: proxyUrl ? await Actor.createProxyConfiguration({ proxyUrls: [proxyUrl] }) : undefined,
        async requestHandler({ page, log }) {
            await applyNetworkBlocker(page);
            log.info(`[Keyword Search] Querying "${keyword}" inside scope: ${subreddit || 'GLOBAL'}`);
            
            await page.goto(searchUrl, { waitUntil: 'domcontentloaded' });
            await page.waitForSelector('a[data-testid="post-title"]', { timeout: 10000 }).catch(() => {});

            const extracted = await page.evaluate(() => {
                return Array.from(document.querySelectorAll('a[data-testid="post-title"]')).map((el, i) => {
                    const container = el.closest('div[data-testid="search-post-container"]') || el.closest('div');
                    const subEl = container?.querySelector('a[href^="/r/"]');
                    const subName = subEl?.getAttribute('href')?.split('/')[2] || 'unknown';

                    // Parse available structural metadata directly out of search results cards
                    const faceplateMetadata = container?.querySelectorAll('span[style*="color"]');
                    let dynamicScore = 0;
                    let dynamicCommentsCount = 0;

                    if (faceplateMetadata && faceplateMetadata.length >= 2) {
                        dynamicScore = parseInt(faceplateMetadata[0].textContent?.replace(/[^0-9]/g, '') || '0', 10);
                        dynamicCommentsCount = parseInt(faceplateMetadata[1].textContent?.replace(/[^0-9]/g, '') || '0', 10);
                    }

                    return {
                        id: `search-${i}-${Date.now()}`,
                        title: el.textContent?.trim() || '',
                        permalink: el.getAttribute('href') || '',
                        subreddit: subName,
                        score: dynamicScore,
                        comments_count: dynamicCommentsCount
                    };
                });
            });

            for (const p of extracted.slice(0, targetLimit)) {
                allItems.push({
                    source: 'reddit',
                    external_id: p.id,
                    title: p.title,
                    content: '', 
                    author: 'unknown',
                    url: p.permalink.startsWith('http') ? p.permalink : `https://www.reddit.com${p.permalink}`,
                    score: p.score,
                    comments_count: p.comments_count,
                    post_type: 'post',
                    subreddit: subreddit || p.subreddit,
                    matched_keyword: keyword, 
                    created_at_platform: Math.floor(Date.now() / 1000),
                    fetched_at: fetchedAt,
                    comments: []
                });
            }
        }
    });

    await crawler.run([searchUrl]);
    return allItems;
}

/**
 * Deep-Dive Secondary Extraction: Fetches comments and body contents from individual URLs
 */
export async function populatePostDetailsAndComments({ item, commentsLimit, proxyUrl }) {
    const crawler = new PlaywrightCrawler({
        maxRequestsPerCrawl: 1,
        headless: true,
        proxyConfiguration: proxyUrl ? await Actor.createProxyConfiguration({ proxyUrls: [proxyUrl] }) : undefined,
        async requestHandler({ page, log }) {
            await applyNetworkBlocker(page);
            
            await page.goto(item.url, { waitUntil: 'domcontentloaded' });
            await page.waitForSelector('shreddit-comment', { timeout: 6000 }).catch(() => {});

            const detailData = await page.evaluate(() => {
                const bodyContainer = document.querySelector('shreddit-post [id*="-post-rtjson-content"]');
                const bodyText = bodyContainer ? bodyContainer.textContent?.trim() : '';

                const commentNodes = Array.from(document.querySelectorAll('shreddit-comment'));
                const commentsParsed = commentNodes.map(el => ({
                    comment_id: el.getAttribute('thingid') || '',
                    author: el.getAttribute('author') || 'unknown',
                    score: parseInt(el.getAttribute('score') || '0', 10),
                    content: el.querySelector('[id*="-comment-rtjson-content"]')?.textContent?.trim() || ''
                }));

                return { bodyText, commentsParsed };
            });

            if (detailData.bodyText && !item.content) {
                item.content = detailData.bodyText;
            }
            item.comments = detailData.commentsParsed.slice(0, commentsLimit);
        }
    });

    await crawler.run([item.url]);
    return item;
}