package scraper

import (
	"encoding/json"
	"log"
	"net/http"
)

type ScrapeRequest struct {
	Query string `json:"query"`
}

type ScrapedItem struct {
	Title string `json:"title"`
	URL   string `json:"url"`
}

func HandleScrape(w http.ResponseWriter, r *http.Request) {
	var req ScrapeRequest
	json.NewDecoder(r.Body).Decode(&req)

	// Just print
	log.Println("Scrape endpoint hit!")

	// TODO:
	// Call Reddit + HN + RSS concurrently
	// Merge results

	results := []ScrapedItem{
		{Title: "Example Post", URL: "https://example.com"},
	}

	json.NewEncoder(w).Encode(results)
}
