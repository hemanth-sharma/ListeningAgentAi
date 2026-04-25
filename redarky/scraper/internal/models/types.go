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
	Subreddits []string `json:"subreddits"`
}
