package reddit

import (
	"encoding/json"
	"fmt"
	"net/http"
	"redarky/internal/models"
	"time"
)

type RedditResponse struct {
	Data struct {
		Children []struct {
			Data struct {
				ID       string `json:"id"`
				Title    string `json:"title"`
				Selftext string `json:"selftext"`
				URL      string `json:"url"`
				Author   string `json:"author"`
				Score    int    `json:"score"`
			} `json:"data"`
		} `json:"children"`
	} `json:"data"`
}

func FetchReddit(subreddit string) ([]models.ScrapedItem, error) {
	url := fmt.Sprintf("https://www.reddit.com/r/%s/hot.json?limit=10", subreddit)

	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return nil, err
	}
	req.Header.Set("User-Agent", "vantage-bot")

	client := &http.Client{Timeout: 10 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("reddit returned status %d", resp.StatusCode)
	}

	var data RedditResponse
	if err := json.NewDecoder(resp.Body).Decode(&data); err != nil {
		return nil, err
	}

	var results []models.ScrapedItem

	for _, post := range data.Data.Children {
		p := post.Data

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
