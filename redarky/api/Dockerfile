version: "3.9"

services:
  api:
    build: ./api
    ports:
      - "8000:8000"
    depends_on:
      - db
      - scraper

  scraper:
    build: ./scraper
    ports:
      - "8081:8081"

  db:
    image: postgres:16
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: redarky
    ports:
      - "5432:5432"

  redis:
    image: redis:7
    ports:
      - "6379:6379"