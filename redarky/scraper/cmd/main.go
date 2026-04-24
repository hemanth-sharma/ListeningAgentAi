package main

import (
	"log"
	"net/http"
	"redarky/internal/scraper"
)

func main() {
	http.HandleFunc("/scrape", scraper.HandleScrape)

	log.Println("Scraper running on :8081")
	log.Fatal(http.ListenAndServe(":8081", nil))
}
