.PHONY: build up down

install:
	pip3 install -r bot/requirements.txt

build:
	pip3 install -r bot/requirements.txt
	docker-compose build

up:
	docker-compose up -d
	echo "[INFO] Leaving some delay (10s) before starting an applications for databases to initialize"
	sleep 10
	python3 bot/main.py

run:
	python3 bot/main.py

down:
	docker-compose down
