package reddit

import (
	"encoding/json"
	"fmt"
	"net/http"
	"net/url"
	"redarky/internal/models"
	"time"
)

type RedditResponse struct {
	Data struct {
		Children []struct {
			Data struct {
				ID         string  `json:"id"`
				Title      string  `json:"title"`
				Selftext   string  `json:"selftext"`
				URL        string  `json:"url"`
				Author     string  `json:"author"`
				Score      int     `json:"score"`
				CreatedUtc float64 `json:"created_utc"`
			} `json:"data"`
		} `json:"children"`
	} `json:"data"`
}

func FetchReddit(subreddit string, query string, since int64) ([]models.ScrapedItem, error) {
	var targetURL string
	escapedQuery := url.QueryEscape(query)

	// Determine if this is a 1-minute cron check or a historical backfill
	// If 'since' looks back more than a few hours, use relevance sorting over a month window
	timeDifference := time.Now().Unix() - since
	timeParam := "all"
	sortParam := "new"

	if timeDifference > 86400 { // Greater than 24 hours -> Backfill mode
		sortParam = "relevance"
		timeParam = "month"
	}

	if subreddit != "" {
		targetURL = fmt.Sprintf("https://www.reddit.com/r/%s/search.json?q=%s&restrict_sr=1&sort=%s&t=%s&limit=100", subreddit, escapedQuery, sortParam, timeParam)
	} else {
		targetURL = fmt.Sprintf("https://www.reddit.com/search.json?q=%s&sort=%s&t=%s&limit=100", escapedQuery, sortParam, timeParam)
	}

	req, err := http.NewRequest("GET", targetURL, nil)
	if err != nil {
		return nil, err
	}
	req.Header.Set("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) RedArkyBot/3.0")

	client := &http.Client{Timeout: 10 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("reddit access error: status %d", resp.StatusCode)
	}

	var data RedditResponse
	if err := json.NewDecoder(resp.Body).Decode(&data); err != nil {
		return nil, err
	}

	var results []models.ScrapedItem
	for _, post := range data.Data.Children {
		p := post.Data

		// Enforce strict time floor boundary filtering
		if int64(p.CreatedUtc) < since {
			continue
		}

		results = append(results, models.ScrapedItem{
			Source:     "reddit",
			ExternalID: p.ID,
			Title:      p.Title,
			Content:    p.Selftext,
			URL:        p.URL,
			Author:     p.Author,
			Score:      p.Score,
			ScrapedAt:  time.Now().Format(time.RFC3339),
		})
	}
	return results, nil
}
