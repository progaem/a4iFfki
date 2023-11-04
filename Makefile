.PHONY: build up down

run:
	python3 bot/bot.py

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down
