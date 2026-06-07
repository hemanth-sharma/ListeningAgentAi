package hn

import (
	"encoding/json"
	"fmt"
	"net/http"
	"net/url"
	"redarky/internal/models"
	"time"
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

func FetchHN(query string) ([]models.ScrapedItem, error) {
	url := fmt.Sprintf("https://hn.algolia.com/api/v1/search?query=%s", url.QueryEscape(query))

	client := &http.Client{Timeout: 10 * time.Second}
	resp, err := client.Get(url)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("hn returned status %d", resp.StatusCode)
	}

	var data HNResponse
	if err := json.NewDecoder(resp.Body).Decode(&data); err != nil {
		return nil, err
	}

	var results []models.ScrapedItem

	for _, item := range data.Hits {
		results = append(results, models.ScrapedItem{
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
