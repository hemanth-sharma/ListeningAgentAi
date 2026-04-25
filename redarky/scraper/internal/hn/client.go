package hn

import (
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"redarky/internal/scraper"
)

type HNResponse struct {
	Hits []struct {
		ObjectID  string `json:"objectID"`
		Title     string `json:"title"`
		URL       string `json:"url"`
		Author    string `json:"author"`
		Points    int    `json:"points"`
		StoryText string `json:"story_text"`
	} `json:"hits"`
}

func FetchHN(query string) ([]scraper.ScrapedItem, error) {
	url := fmt.Sprintf("https://hn.algolia.com/api/v1/search?query=%s", query)

	resp, err := http.Get(url)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	var data HNResponse
	json.NewDecoder(resp.Body).Decode(&data)

	var results []scraper.ScrapedItem

	for _, item := range data.Hits {
		results = append(results, scraper.ScrapedItem{
			Source:     "hn",
			ExternalID: item.ObjectID,
			Title:      item.Title,
			Content:    item.StoryText,
			URL:        item.URL,
			Author:     item.Author,
			Score:      item.Points,
			ScrapedAt:  time.Now().Format(time.RFC3339),
		})
	}

	return results, nil
}
