package hn

import (
	"encoding/json"
	"fmt"
	"net/http"
	"net/url"
	"redarky/internal/models"
	"strings"
	"time"
)

type hnResponse struct {
	Hits []struct {
		ObjectID    string   `json:"objectID"`
		Title       string   `json:"title"`
		URL         string   `json:"url"` // only populated on stories
		Author      string   `json:"author"`
		Points      int      `json:"points"`
		StoryText   string   `json:"story_text"`   // self-text for Ask HN / Show HN
		CommentText string   `json:"comment_text"` // populated for comments
		StoryID     int64    `json:"story_id"`     // parent story ID for comments
		Tags        []string `json:"_tags"`
		CreatedAtI  int64    `json:"created_at_i"` // Unix timestamp
	} `json:"hits"`
}

var httpClient = &http.Client{Timeout: 12 * time.Second}

// FetchHN queries the HN Algolia API for items (stories + comments) matching
// the given query, created on or after `since`.
//
// The Algolia endpoint is free, has no meaningful rate limit for our scale,
// and supports timestamp-based filtering natively — so we rely on it rather
// than client-side filtering for the time gate.
func FetchHN(query string, since int64, excludeKeywords []string) ([]models.ScrapedItem, error) {
	// search_by_date returns results sorted by creation time (newest first),
	// which is exactly what we want for live polling.
	rawURL := fmt.Sprintf(
		"https://hn.algolia.com/api/v1/search_by_date?query=%s&numericFilters=created_at_i>=%d&tags=(story,comment)&hitsPerPage=100",
		url.QueryEscape(query),
		since,
	)

	resp, err := httpClient.Get(rawURL)
	if err != nil {
		return nil, fmt.Errorf("HN fetch error: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("HN returned status %d", resp.StatusCode)
	}

	var data hnResponse
	if err := json.NewDecoder(resp.Body).Decode(&data); err != nil {
		return nil, fmt.Errorf("HN JSON decode: %w", err)
	}

	now := time.Now().Format(time.RFC3339)
	var results []models.ScrapedItem

	for _, hit := range data.Hits {
		// --- Determine post type from Algolia _tags ---
		postType := "post"
		for _, tag := range hit.Tags {
			if tag == "comment" {
				postType = "comment"
				break
			}
		}

		// --- Resolve content and URL correctly per type ---
		content := hit.StoryText
		itemURL := hit.URL

		if postType == "comment" {
			content = hit.CommentText
			// For comments, the canonical URL is the thread with the comment anchored.
			// hit.URL is empty for comments; construct from story_id.
			if hit.StoryID != 0 {
				itemURL = fmt.Sprintf("https://news.ycombinator.com/item?id=%s", hit.ObjectID)
			} else {
				itemURL = fmt.Sprintf("https://news.ycombinator.com/item?id=%s", hit.ObjectID)
			}
		}

		// Fall back to HN item URL for stories without an external URL (Ask HN etc.)
		if itemURL == "" {
			itemURL = fmt.Sprintf("https://news.ycombinator.com/item?id=%s", hit.ObjectID)
		}

		// --- Title for comments ---
		title := hit.Title
		if postType == "comment" && title == "" {
			title = "(HN comment)"
		}

		// --- Exclude keyword filter ---
		textToCheck := strings.ToLower(title + " " + content)
		if containsAny(textToCheck, excludeKeywords) {
			continue
		}

		results = append(results, models.ScrapedItem{
			Source:     "hn",
			ExternalID: hit.ObjectID,
			Title:      title,
			Content:    content,
			URL:        itemURL,
			Author:     hit.Author,
			Score:      hit.Points,
			Subreddit:  "",
			PostType:   postType,
			CreatedAt:  hit.CreatedAtI,
			ScrapedAt:  now,
		})
	}

	return results, nil
}

func containsAny(text string, keywords []string) bool {
	for _, kw := range keywords {
		if strings.Contains(text, strings.ToLower(kw)) {
			return true
		}
	}
	return false
}
