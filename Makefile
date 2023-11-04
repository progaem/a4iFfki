.PHONY: build up down

build:
	pip3 install -r bot/requirements.txt
	docker-compose build

up:
	docker-compose up -d
	python3 bot/main.py

down:
	docker-compose down
