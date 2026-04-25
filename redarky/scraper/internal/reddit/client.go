package reddit

import (
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"redarky/internal/scraper"
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

func FetchReddit(subreddit string) ([]scraper.ScrapedItem, error) {
	url := fmt.Sprintf("https://www.reddit.com/r/%s/hot.json?limit=10", subreddit)

	req, _ := http.NewRequest("GET", url, nil)
	req.Header.Set("User-Agent", "vantage-bot")

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	var data RedditResponse
	json.NewDecoder(resp.Body).Decode(&data)

	var results []scraper.ScrapedItem

	for _, post := range data.Data.Children {
		p := post.Data

		results = append(results, scraper.ScrapedItem{
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
