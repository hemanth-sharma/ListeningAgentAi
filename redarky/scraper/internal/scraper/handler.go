package scraper

import (
	"context"
	"encoding/json"
	"errors"
	"net/http"
	"sync"
	"time"

	"redarky/internal/hn"
	"redarky/internal/models"
	"redarky/internal/reddit"

	"github.com/sony/gobreaker"
	"golang.org/x/time/rate"
)

type sourceResult struct {
	items []models.ScrapedItem
	err   error
}

var (
	limiters = map[string]*rate.Limiter{
		"hn":     rate.NewLimiter(rate.Every(500*time.Millisecond), 2),
		"reddit": rate.NewLimiter(rate.Every(1000*time.Millisecond), 1),
	}
	breakers = map[string]*gobreaker.CircuitBreaker{
		"hn":     gobreaker.NewCircuitBreaker(gobreaker.Settings{Name: "hn-source", MaxRequests: 2, Interval: 30 * time.Second, Timeout: 15 * time.Second}),
		"reddit": gobreaker.NewCircuitBreaker(gobreaker.Settings{Name: "reddit-source", MaxRequests: 2, Interval: 30 * time.Second, Timeout: 15 * time.Second}),
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
	result, err := breaker.Execute(func() (interface{}, error) { return fetchFn() })
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

	var req models.ScrapeRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "invalid request body", http.StatusBadRequest)
		return
	}
	if req.Query == "" {
		http.Error(w, "query is required", http.StatusBadRequest)
		return
	}

	// Default window: Look back 30 days if timestamp floor boundary isn't sent
	if req.Since == 0 {
		req.Since = time.Now().AddDate(0, 0, -30).Unix()
	}

	var wg sync.WaitGroup
	resultsChan := make(chan sourceResult, len(req.Subreddits)+2)

	// Check if platform configuration wants HN tracking
	hasPlatform := func(p string) bool {
		for _, pl := range req.Platforms {
			if pl == p {
				return true
			}
		}
		return false
	}

	if hasPlatform("hn") {
		wg.Add(1)
		go func() {
			defer wg.Done()
			data, err := guardedFetch("hn", func() ([]models.ScrapedItem, error) {
				return hn.FetchHN(req.Query, req.Since)
			})
			resultsChan <- sourceResult{items: data, err: err}
		}()
	}

	if hasPlatform("reddit") {
		if len(req.Subreddits) > 0 {
			for _, sub := range req.Subreddits {
				wg.Add(1)
				go func(s string) {
					defer wg.Done()
					data, err := guardedFetch("reddit", func() ([]models.ScrapedItem, error) {
						return reddit.FetchReddit(s, req.Query, req.Since)
					})
					resultsChan <- sourceResult{items: data, err: err}
				}(sub)
			}
		} else {
			wg.Add(1)
			go func() {
				defer wg.Done()
				data, err := guardedFetch("reddit", func() ([]models.ScrapedItem, error) {
					return reddit.FetchReddit("", req.Query, req.Since)
				})
				resultsChan <- sourceResult{items: data, err: err}
			}()
		}
	}

	go func() {
		wg.Wait()
		close(resultsChan)
	}()

	var allResults []models.ScrapedItem
	for res := range resultsChan {
		if res.err == nil {
			allResults = append(allResults, res.items...)
		}
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(allResults)
}
