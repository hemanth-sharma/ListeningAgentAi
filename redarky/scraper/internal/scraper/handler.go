package scraper

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"net/http"
	"strings"
	"sync"
	"time"

	"redarky/internal/hn"
	"redarky/internal/models"
	"redarky/internal/reddit"

	"github.com/sony/gobreaker"
	"golang.org/x/time/rate"
)

// ── Rate limiters ──────────────────────────────────────────────────────────────
//
// Reddit public API: ~60 requests/minute unauthenticated.
// We allow 1 req/sec with a burst of 3 — conservative for safety.
//
// HN Algolia: no published limit; we use 5 req/sec with burst 10.
// Adjust these if you integrate OAuth for Reddit later.

var (
	redditLimiter = rate.NewLimiter(rate.Every(1100*time.Millisecond), 3)
	hnLimiter     = rate.NewLimiter(rate.Every(200*time.Millisecond), 10)
)

// ── Circuit breakers ───────────────────────────────────────────────────────────
//
// If a source returns 3 consecutive errors, the breaker opens for 30 seconds.
// This prevents goroutine pileup when Reddit is rate-limiting us.

var (
	redditBreaker = gobreaker.NewCircuitBreaker(gobreaker.Settings{
		Name:        "reddit",
		MaxRequests: 3,
		Interval:    60 * time.Second,
		Timeout:     30 * time.Second,
		ReadyToTrip: func(counts gobreaker.Counts) bool {
			return counts.ConsecutiveFailures >= 3
		},
	})
	hnBreaker = gobreaker.NewCircuitBreaker(gobreaker.Settings{
		Name:        "hn",
		MaxRequests: 5,
		Interval:    60 * time.Second,
		Timeout:     20 * time.Second,
		ReadyToTrip: func(counts gobreaker.Counts) bool {
			return counts.ConsecutiveFailures >= 3
		},
	})
)

// fetchJob is one unit of work dispatched to a goroutine.
type fetchJob struct {
	source    string // "reddit" | "hn"
	keyword   string // the include/brand keyword that triggered this job
	isBrand   bool   // true if this keyword came from BrandKeywords
	subreddit string // "" means Reddit-wide or HN
}

// fetchResult is what a goroutine sends back on the results channel.
type fetchResult struct {
	items  []models.ScrapedItem
	srcErr *models.SourceError
}

// HandleScrape is the HTTP handler for POST /scrape.
//
// Design:
//  1. Parse + validate request.
//  2. Expand request into one fetchJob per (keyword × subreddit) pair.
//  3. Dispatch all jobs concurrently, respecting rate limits + circuit breakers.
//  4. Merge results; deduplicate by (source, external_id) within this response.
//  5. Tag each item with which keyword matched and whether it's a brand mention.
//  6. Return ScrapeResult JSON.
func HandleScrape(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var req models.ScrapeRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "invalid JSON body: "+err.Error(), http.StatusBadRequest)
		return
	}
	if err := validateRequest(&req); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	applyDefaults(&req)

	// ── Build the job list ────────────────────────────────────────────────────
	jobs := buildJobs(&req)
	if len(jobs) == 0 {
		writeJSON(w, models.ScrapeResult{Items: []models.ScrapedItem{}})
		return
	}

	// ── Fan-out: one goroutine per job ────────────────────────────────────────
	resultsCh := make(chan fetchResult, len(jobs))
	var wg sync.WaitGroup

	for _, job := range jobs {
		wg.Add(1)
		go func(j fetchJob) {
			defer wg.Done()
			items, srcErr := executeJob(j, &req)
			resultsCh <- fetchResult{items: items, srcErr: srcErr}
		}(job)
	}

	// Close channel once all goroutines finish.
	go func() {
		wg.Wait()
		close(resultsCh)
	}()

	// ── Collect results ───────────────────────────────────────────────────────
	seen := make(map[string]struct{}) // dedup key: "source:external_id"
	var allItems []models.ScrapedItem
	var allErrors []models.SourceError

	for res := range resultsCh {
		if res.srcErr != nil {
			allErrors = append(allErrors, *res.srcErr)
		}
		for _, item := range res.items {
			key := item.Source + ":" + item.ExternalID
			if _, exists := seen[key]; exists {
				continue // same post matched by multiple keywords — keep first
			}
			seen[key] = struct{}{}
			allItems = append(allItems, item)
		}
	}

	writeJSON(w, models.ScrapeResult{
		Items:  allItems,
		Errors: allErrors,
	})
}

// buildJobs expands the request into individual fetch units.
//
// Rules:
//   - Each include keyword × each subreddit = 1 Reddit job
//   - If no subreddits specified, each include keyword = 1 Reddit-wide job
//   - Brand keywords follow the same subreddit expansion but are flagged isBrand=true
//   - HN always receives 1 job per unique keyword (no subreddit concept)
func buildJobs(req *models.ScrapeRequest) []fetchJob {
	var jobs []fetchJob
	wantsReddit := hasPlatform(req.Platforms, "reddit")
	wantsHN := hasPlatform(req.Platforms, "hn")

	allKeywords := make([]struct {
		kw      string
		isBrand bool
	}, 0, len(req.IncludeKeywords)+len(req.BrandKeywords))

	for _, kw := range req.IncludeKeywords {
		allKeywords = append(allKeywords, struct {
			kw      string
			isBrand bool
		}{kw, false})
	}
	for _, kw := range req.BrandKeywords {
		allKeywords = append(allKeywords, struct {
			kw      string
			isBrand bool
		}{kw, true})
	}

	for _, kwEntry := range allKeywords {
		// ── Reddit jobs ───────────────────────────────────────────────────────
		if wantsReddit {
			if len(req.Subreddits) > 0 {
				for _, sub := range req.Subreddits {
					jobs = append(jobs, fetchJob{
						source:    "reddit",
						keyword:   kwEntry.kw,
						isBrand:   kwEntry.isBrand,
						subreddit: sub,
					})
				}
			} else {
				jobs = append(jobs, fetchJob{
					source:  "reddit",
					keyword: kwEntry.kw,
					isBrand: kwEntry.isBrand,
				})
			}
		}

		// ── HN jobs ───────────────────────────────────────────────────────────
		if wantsHN {
			jobs = append(jobs, fetchJob{
				source:  "hn",
				keyword: kwEntry.kw,
				isBrand: kwEntry.isBrand,
			})
		}
	}

	return jobs
}

// executeJob runs one fetchJob through the rate limiter and circuit breaker.
func executeJob(job fetchJob, req *models.ScrapeRequest) ([]models.ScrapedItem, *models.SourceError) {
	var (
		items []models.ScrapedItem
		err   error
	)

	switch job.source {
	case "reddit":
		items, err = executeReddit(job, req)
	case "hn":
		items, err = executeHN(job, req)
	default:
		return nil, &models.SourceError{
			Source:  job.source,
			Query:   job.keyword,
			Message: "unsupported source",
		}
	}

	if err != nil {
		return nil, &models.SourceError{
			Source:  job.source,
			Query:   job.keyword,
			Message: err.Error(),
		}
	}

	// Tag every item with the keyword that matched and whether it's a brand mention.
	for i := range items {
		items[i].MatchedKeyword = job.keyword
		items[i].IsBrandMention = job.isBrand
	}

	return items, nil
}

func executeReddit(job fetchJob, req *models.ScrapeRequest) ([]models.ScrapedItem, error) {
	// Wait for rate limiter slot (blocks goroutine, not OS thread).
	ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
	defer cancel()
	if err := redditLimiter.Wait(ctx); err != nil {
		return nil, fmt.Errorf("reddit rate limiter: %w", err)
	}

	// Execute through circuit breaker.
	result, err := redditBreaker.Execute(func() (interface{}, error) {
		if job.subreddit != "" {
			return reddit.FetchSubredditNew(job.subreddit, job.keyword, req.Since, req.ExcludeKeywords)
		}
		return reddit.FetchRedditWide(job.keyword, req.Since, req.Mode, req.ExcludeKeywords)
	})
	if err != nil {
		if errors.Is(err, gobreaker.ErrOpenState) {
			return nil, fmt.Errorf("reddit circuit open — source temporarily unavailable")
		}
		return nil, err
	}

	items, ok := result.([]models.ScrapedItem)
	if !ok {
		return nil, fmt.Errorf("reddit: unexpected result type")
	}
	return items, nil
}

func executeHN(job fetchJob, req *models.ScrapeRequest) ([]models.ScrapedItem, error) {
	ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
	defer cancel()
	if err := hnLimiter.Wait(ctx); err != nil {
		return nil, fmt.Errorf("HN rate limiter: %w", err)
	}

	result, err := hnBreaker.Execute(func() (interface{}, error) {
		return hn.FetchHN(job.keyword, req.Since, req.ExcludeKeywords)
	})
	if err != nil {
		if errors.Is(err, gobreaker.ErrOpenState) {
			return nil, fmt.Errorf("HN circuit open — source temporarily unavailable")
		}
		return nil, err
	}

	items, ok := result.([]models.ScrapedItem)
	if !ok {
		return nil, fmt.Errorf("HN: unexpected result type")
	}
	return items, nil
}

// ── Helpers ────────────────────────────────────────────────────────────────────

func validateRequest(req *models.ScrapeRequest) error {
	if len(req.IncludeKeywords) == 0 && len(req.BrandKeywords) == 0 {
		return errors.New("at least one include_keyword or brand_keyword is required")
	}
	if len(req.Platforms) == 0 {
		return errors.New("at least one platform is required")
	}
	for _, kw := range req.IncludeKeywords {
		if strings.TrimSpace(kw) == "" {
			return errors.New("include_keywords must not contain empty strings")
		}
	}
	return nil
}

func applyDefaults(req *models.ScrapeRequest) {
	// Default mode: live (for recurring polls)
	if req.Mode == "" {
		req.Mode = models.ModeLive
	}

	// Default Since: for live mode, look back 5 minutes (typical poll interval).
	// For backfill, look back 30 days.
	// Python should always send an explicit Since, but this is a safe fallback.
	if req.Since == 0 {
		switch req.Mode {
		case models.ModeLive:
			req.Since = time.Now().Add(-5 * time.Minute).Unix()
		case models.ModeBackfill:
			req.Since = time.Now().AddDate(0, 0, -30).Unix()
		}
	}
}

func hasPlatform(platforms []string, target string) bool {
	for _, p := range platforms {
		if strings.EqualFold(p, target) {
			return true
		}
	}
	return false
}

func writeJSON(w http.ResponseWriter, v any) {
	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(v); err != nil {
		http.Error(w, "failed to encode response", http.StatusInternalServerError)
	}
}
