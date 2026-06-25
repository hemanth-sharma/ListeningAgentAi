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
		ObjectID    string `json:"objectID"`
		Title       string `json:"title"`
		URL         string `json:"url"`
		Author      string `json:"author"`
		Points      int    `json:"points"`
		StoryText   string `json:"story_text"`
		CommentText string `json:"comment_text"`
	} `json:"hits"`
}

func FetchHN(query string, since int64) ([]models.ScrapedItem, error) {
	// target search_by_date and inject creation timestamp condition filters directly
	targetURL := fmt.Sprintf("https://hn.algolia.com/api/v1/search_by_date?query=%s&numericFilters=created_at_i>=%d&tags=(story,comment)", url.QueryEscape(query), since)

	client := &http.Client{Timeout: 10 * time.Second}
	resp, err := client.Get(targetURL)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("hn error: status %d", resp.StatusCode)
	}

	var data HNResponse
	if err := json.NewDecoder(resp.Body).Decode(&data); err != nil {
		return nil, err
	}

	var results []models.ScrapedItem
	for _, item := range data.Hits {
		content := item.StoryText
		if content == "" {
			content = item.CommentText
		}

		results = append(results, models.ScrapedItem{
			Source:     "hn",
			ExternalID: item.ObjectID,
			Title:      item.Title,
			Content:    content,
			URL:        fmt.Sprintf("https://news.ycombinator.com/item?id=%s", item.ObjectID),
			Author:     item.Author,
			Score:      item.Points,
			ScrapedAt:  time.Now().Format(time.RFC3339),
		})
	}
	return results, nil
}
