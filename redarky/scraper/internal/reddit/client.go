package reddit

import (
	"encoding/json"
	"fmt"
	"net/http"
	"net/url"
	"redarky/internal/models"
	"strings"
	"time"
)

// redditListing is the top-level JSON envelope from the Reddit API.
type redditListing struct {
	Data struct {
		Children []struct {
			Kind string `json:"kind"` // "t3" = post, "t1" = comment
			Data struct {
				ID         string  `json:"id"`
				Name       string  `json:"name"`     // full ID e.g. t3_abc123
				Title      string  `json:"title"`    // posts only
				Selftext   string  `json:"selftext"` // posts only
				Body       string  `json:"body"`     // comments only
				URL        string  `json:"url"`
				Permalink  string  `json:"permalink"`
				Author     string  `json:"author"`
				Score      int     `json:"score"`
				Subreddit  string  `json:"subreddit"`
				CreatedUtc float64 `json:"created_utc"`
				IsVideo    bool    `json:"is_video"`
				IsSelf     bool    `json:"is_self"`
			} `json:"data"`
		} `json:"children"`
	} `json:"data"`
}

// httpClient is reused across all calls — one per process, not per request.
var httpClient = &http.Client{Timeout: 12 * time.Second}

// FetchSubredditNew polls r/subreddit/new.json for the most recent posts.
// This is the correct endpoint for live streaming — sort=new gives us the
// freshest items with no ranking noise.
//
// We filter client-side by `since` so we don't surface old posts when
// the subreddit is low-traffic and we receive items older than our window.
func FetchSubredditNew(subreddit, query string, since int64, excludeKeywords []string) ([]models.ScrapedItem, error) {
	var rawURL string
	if query != "" {
		// Scoped search within a subreddit, sorted by newest
		rawURL = fmt.Sprintf(
			"https://www.reddit.com/r/%s/search.json?q=%s&restrict_sr=1&sort=new&t=day&limit=100",
			url.PathEscape(subreddit),
			url.QueryEscape(query),
		)
	} else {
		// No query — just pull the raw new feed (used for brand monitoring
		// where we search the whole subreddit for a brand name mention)
		rawURL = fmt.Sprintf(
			"https://www.reddit.com/r/%s/new.json?limit=100",
			url.PathEscape(subreddit),
		)
	}

	items, err := fetchAndParse(rawURL, since, excludeKeywords)
	if err != nil {
		return nil, fmt.Errorf("subreddit %q query %q: %w", subreddit, query, err)
	}
	return items, nil
}

// FetchRedditWide searches Reddit-wide (not scoped to a subreddit).
// Used when the user has not specified any target subreddits.
func FetchRedditWide(query string, since int64, mode models.ScrapeMode, excludeKeywords []string) ([]models.ScrapedItem, error) {
	sortParam := "new"
	timeParam := "day"
	if mode == models.ModeBackfill {
		sortParam = "relevance"
		timeParam = "month"
	}

	rawURL := fmt.Sprintf(
		"https://www.reddit.com/search.json?q=%s&sort=%s&t=%s&limit=100",
		url.QueryEscape(query),
		sortParam,
		timeParam,
	)

	items, err := fetchAndParse(rawURL, since, excludeKeywords)
	if err != nil {
		return nil, fmt.Errorf("reddit-wide query %q: %w", query, err)
	}
	return items, nil
}

// fetchAndParse is the shared HTTP + parse + filter logic.
func fetchAndParse(rawURL string, since int64, excludeKeywords []string) ([]models.ScrapedItem, error) {
	req, err := http.NewRequest(http.MethodGet, rawURL, nil)
	if err != nil {
		return nil, err
	}
	// Reddit blocks the default Go UA; impersonate a browser.
	// req.Header.Set("User-Agent", "Mozilla/5.0 (compatible; RedarkyBot/3.0; +https://redarky.com/bot)")
	// req.Header.Set("Accept", "application/json")

	req.Header.Set("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
	req.Header.Set("Accept", "application/json, text/plain, */*")
	req.Header.Set("Accept-Language", "en-US,en;q=0.9")

	resp, err := httpClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusTooManyRequests {
		return nil, fmt.Errorf("rate-limited by Reddit (429)")
	}
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("reddit returned status %d", resp.StatusCode)
	}

	var listing redditListing
	if err := json.NewDecoder(resp.Body).Decode(&listing); err != nil {
		return nil, fmt.Errorf("JSON decode: %w", err)
	}

	now := time.Now().Format(time.RFC3339)
	var results []models.ScrapedItem

	for _, child := range listing.Data.Children {
		d := child.Data

		// --- Time gate: drop anything older than `since` ---
		if int64(d.CreatedUtc) < since {
			continue
		}

		// --- Exclude keyword filter (client-side, zero API cost) ---
		textToCheck := strings.ToLower(d.Title + " " + d.Selftext + " " + d.Body)
		if containsAny(textToCheck, excludeKeywords) {
			continue
		}

		// --- Drop deleted/removed content ---
		if d.Author == "[deleted]" || d.Selftext == "[removed]" {
			continue
		}

		// --- Normalise URL ---
		// For link posts the URL is external; for self posts, construct permalink.
		postURL := d.URL
		if d.IsSelf || d.Permalink != "" {
			postURL = "https://www.reddit.com" + d.Permalink
		}

		// --- Determine post type ---
		postType := "post"
		content := d.Selftext
		title := d.Title
		if child.Kind == "t1" { // comment
			postType = "comment"
			content = d.Body
			title = "(comment)"
			postURL = "https://www.reddit.com" + d.Permalink
		}

		results = append(results, models.ScrapedItem{
			Source:     "reddit",
			ExternalID: d.ID,
			Title:      title,
			Content:    content,
			URL:        postURL,
			Author:     d.Author,
			Score:      d.Score,
			Subreddit:  d.Subreddit,
			PostType:   postType,
			CreatedAt:  int64(d.CreatedUtc),
			ScrapedAt:  now,
		})
	}

	return results, nil
}

// containsAny returns true if text contains any of the given lowercase keywords.
func containsAny(text string, keywords []string) bool {
	for _, kw := range keywords {
		if strings.Contains(text, strings.ToLower(kw)) {
			return true
		}
	}
	return false
}
