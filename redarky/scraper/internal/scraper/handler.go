package scraper

import (
	"context"
	"encoding/json"
	"errors"
	"net/http"
	"sync"
	"time"

	"github.com/sony/gobreaker"
	"golang.org/x/time/rate"
	"redarky/internal/hn"
	"redarky/internal/models"
	"redarky/internal/reddit"
)

type ScrapeRequest struct {
	Query      string   `json:"query"`
	Subreddits []string `json:"subreddits"`
}

type sourceResult struct {
	items []models.ScrapedItem
	err   error
}

var (
	limiters = map[string]*rate.Limiter{
		"hn":     rate.NewLimiter(rate.Every(500*time.Millisecond), 2),
		"reddit": rate.NewLimiter(rate.Every(700*time.Millisecond), 2),
	}
	breakers = map[string]*gobreaker.CircuitBreaker{
		"hn": gobreaker.NewCircuitBreaker(gobreaker.Settings{
			Name:        "hn-source",
			MaxRequests: 2,
			Interval:    30 * time.Second,
			Timeout:     15 * time.Second,
		}),
		"reddit": gobreaker.NewCircuitBreaker(gobreaker.Settings{
			Name:        "reddit-source",
			MaxRequests: 2,
			Interval:    30 * time.Second,
			Timeout:     15 * time.Second,
		}),
	}
)

func guardedFetch(source string, fetchFn func() ([]models.ScrapedItem, error)) ([]models.ScrapedItem, error) {
	limiter, ok := limiters[source]
	if !ok {
		return nil, errors.New("unknown source limiter")
	}
	if err := limiter.Wait(context.Background()); err != nil {
		return nil, err
	}

	breaker, ok := breakers[source]
	if !ok {
		return nil, errors.New("unknown source circuit breaker")
	}
	result, err := breaker.Execute(func() (interface{}, error) {
		return fetchFn()
	})
	if err != nil {
		return nil, err
	}
	items, ok := result.([]models.ScrapedItem)
	if !ok {
		return nil, errors.New("invalid result type")
	}
	return items, nil
}

func HandleScrape(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var req ScrapeRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "invalid request body", http.StatusBadRequest)
		return
	}
	if req.Query == "" {
		http.Error(w, "query is required", http.StatusBadRequest)
		return
	}

	var wg sync.WaitGroup
	resultsChan := make(chan sourceResult, len(req.Subreddits)+1)

	// HN goroutine
	wg.Add(1)
	go func() {
		defer wg.Done()
		data, err := guardedFetch("hn", func() ([]models.ScrapedItem, error) {
			return hn.FetchHN(req.Query)
		})
		resultsChan <- sourceResult{items: data, err: err}
	}()

	// Reddit goroutines
	for _, sub := range req.Subreddits {
		wg.Add(1)
		go func(s string) {
			defer wg.Done()
			data, err := guardedFetch("reddit", func() ([]models.ScrapedItem, error) {
				return reddit.FetchReddit(s)
			})
			resultsChan <- sourceResult{items: data, err: err}
		}(sub)
	}

	// Close channel when done
	go func() {
		wg.Wait()
		close(resultsChan)
	}()

	var allResults []models.ScrapedItem
	errorCount := 0

	for res := range resultsChan {
		if res.err != nil {
			errorCount++
			continue
		}
		allResults = append(allResults, res.items...)
	}

	if len(allResults) == 0 && errorCount > 0 {
		http.Error(w, "all sources failed", http.StatusBadGateway)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(allResults)
}
