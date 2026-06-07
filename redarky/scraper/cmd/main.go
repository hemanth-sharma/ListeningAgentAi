package main

import (
	"log"
	"net/http"
	"redarky/internal/scraper"
	"time"
)

func main() {
	mux := http.NewServeMux()
	mux.HandleFunc("/scrape", scraper.HandleScrape)

	log.Println("Scraper running on :8081")
	server := &http.Server{
		Addr:         ":8081",
		Handler:      mux,
		ReadTimeout:  5 * time.Second,
		WriteTimeout: 30 * time.Second,
	}
	log.Fatal(server.ListenAndServe())
}
