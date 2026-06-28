package models

// ScrapeMode controls whether we are doing an initial backfill
// or a live-stream poll (every 1–5 minutes).
type ScrapeMode string

const (
	// ModeLive is used for recurring polls (every 1–5 min).
	// We only want posts created after `Since`, sorted by newest-first.
	ModeLive ScrapeMode = "live"

	// ModeBackfill is used once on project creation to seed history.
	// We want relevance-sorted results over a longer window.
	ModeBackfill ScrapeMode = "backfill"
)

// ScrapeRequest is the JSON body accepted by POST /scrape.
// Python (FastAPI/Celery) sends one of these per project per poll cycle.
type ScrapeRequest struct {
	// ProjectID ties results back to a project for downstream dedup.
	ProjectID string `json:"project_id"`

	// IncludeKeywords: posts must match at least one of these.
	// e.g. ["need app developer", "hire android developer"]
	IncludeKeywords []string `json:"include_keywords"`

	// ExcludeKeywords: posts matching any of these are dropped.
	// Applied AFTER fetching, client-side, so no API cost.
	// e.g. ["python", "musician", "job posting"]
	ExcludeKeywords []string `json:"exclude_keywords"`

	// BrandKeywords: exact brand/competitor names to track separately.
	// These are OR-ed with IncludeKeywords but tagged differently.
	// e.g. ["Redarky", "Syften", "Octolens"]
	BrandKeywords []string `json:"brand_keywords"`

	// Platforms: which sources to poll. Supported: "reddit", "hn".
	// e.g. ["reddit", "hn"]
	Platforms []string `json:"platforms"`

	// Subreddits: if non-empty, Reddit searches are scoped to these.
	// If empty, we search Reddit-wide.
	// e.g. ["forhire", "freelance", "androiddev"]
	Subreddits []string `json:"subreddits"`

	// Since is a Unix timestamp. Only posts created >= Since are returned.
	// For live polls, Python sets this to (now - poll_interval).
	// For backfill, Python sets this to (now - 30 days).
	Since int64 `json:"since"`

	// Mode controls fetch strategy.
	Mode ScrapeMode `json:"mode"`
}

// ScrapedItem is the normalised output record, shared across all sources.
type ScrapedItem struct {
	Source         string `json:"source"`      // "reddit" | "hn"
	ExternalID     string `json:"external_id"` // platform-native ID (Reddit t3_xxx, HN objectID)
	Title          string `json:"title"`
	Content        string `json:"content"` // selftext / story_text / comment_text
	URL            string `json:"url"`     // canonical link to the post/comment
	Author         string `json:"author"`
	Score          int    `json:"score"`            // upvotes / points
	Subreddit      string `json:"subreddit"`        // populated for Reddit, "" for HN
	PostType       string `json:"post_type"`        // "post" | "comment"
	MatchedKeyword string `json:"matched_keyword"`  // which keyword triggered this hit
	IsBrandMention bool   `json:"is_brand_mention"` // true when triggered by a BrandKeyword
	CreatedAt      int64  `json:"created_at"`       // Unix timestamp of original post creation
	ScrapedAt      string `json:"scraped_at"`       // RFC3339 timestamp of when we fetched it
}

// ScrapeResult is the full response body from POST /scrape.
type ScrapeResult struct {
	Items  []ScrapedItem `json:"items"`
	Errors []SourceError `json:"errors,omitempty"`
}

// SourceError captures per-source failures without aborting the whole request.
type SourceError struct {
	Source  string `json:"source"`
	Query   string `json:"query"`
	Message string `json:"message"`
}
