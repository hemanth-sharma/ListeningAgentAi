package scraper

import (
	"encoding/json"
	"net/http"
	"sync"

	"redarky/internal/hn"
	"redarky/internal/models"
	"redarky/internal/reddit"
)

type ScrapeRequest struct {
	Query      string   `json:"query"`
	Subreddits []string `json:"subreddits"`
}

func HandleScrape(w http.ResponseWriter, r *http.Request) {
	var req ScrapeRequest
	json.NewDecoder(r.Body).Decode(&req)

	var wg sync.WaitGroup
	resultsChan := make(chan []models.ScrapedItem)

	// HN goroutine
	wg.Add(1)
	go func() {
		defer wg.Done()
		data, _ := hn.FetchHN(req.Query)
		resultsChan <- data
	}()

	// Reddit goroutines
	for _, sub := range req.Subreddits {
		wg.Add(1)
		go func(s string) {
			defer wg.Done()
			data, _ := reddit.FetchReddit(s)
			resultsChan <- data
		}(sub)
	}

	// Close channel when done
	go func() {
		wg.Wait()
		close(resultsChan)
	}()

	var allResults []models.ScrapedItem

	for res := range resultsChan {
		allResults = append(allResults, res...)
	}

	json.NewEncoder(w).Encode(allResults)
}
