package main

import (
	"log"
	"net/http"
	"redarky/internal/scraper"
	"time"
)

func main() {
	mux := http.NewServeMux()

	// POST /scrape — main data extraction endpoint
	mux.HandleFunc("/scrape", scraper.HandleScrape)

	// GET /health — used by Docker health checks and load balancers
	mux.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(`{"status":"ok","service":"redarky-scraper"}`))
	})

	server := &http.Server{
		Addr:    ":8081",
		Handler: mux,

		// Generous read timeout because our handler fans out many HTTP calls
		// to external APIs before responding. 45s matches the Python httpx timeout.
		ReadTimeout:  10 * time.Second,
		WriteTimeout: 50 * time.Second,
		IdleTimeout:  120 * time.Second,
	}

	log.Println("redarky-scraper listening on :8081")
	log.Fatal(server.ListenAndServe())
}
