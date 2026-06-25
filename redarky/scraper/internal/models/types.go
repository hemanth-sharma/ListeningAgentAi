package models

type ScrapedItem struct {
	Source     string `json:"source"`
	ExternalID string `json:"external_id"`
	Title      string `json:"title"`
	Content    string `json:"content"`
	URL        string `json:"url"`
	Author     string `json:"author"`
	Score      int    `json:"score"`
	ScrapedAt  string `json:"scraped_at"`
}

type ScrapeRequest struct {
	Query      string   `json:"query"`
	Platforms  []string `json:"platforms"`  // e.g., ["reddit", "hn"]
	Subreddits []string `json:"subreddits"` // Targeted subreddits if applicable
	Since      int64    `json:"since"`      // Unix timestamp floor boundary
}
