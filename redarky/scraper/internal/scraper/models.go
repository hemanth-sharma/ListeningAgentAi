// internal/scraper/models.go
package scraper

import "time"

type ScrapedItem struct {
	Source     string    `json:"source"`
	ExternalID string    `json:"external_id"`
	Title      string    `json:"title"`
	Content    string    `json:"content"`
	URL        string    `json:"url"`
	Score      int       `json:"score"`
	Author     string    `json:"author"`
	ScrapedAt  time.Time `json:"scraped_at"`
}

type ScrapeRequest struct {
	MissionID  string   `json:"mission_id"`
	Keywords   []string `json:"keywords"`
	Sources    []string `json:"sources"`
	SubSources []string `json:"subsources"`
}
