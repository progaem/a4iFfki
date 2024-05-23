.PHONY: build up down

install:
	pip3 install -r src/requirements.txt

build:
	pip3 install -r src/requirements.txt
	docker-compose build

up:
	docker-compose up -d
	echo "[INFO] Leaving some delay (10s) before starting an applications for databases to initialize"
	sleep 10
	cd src/ && python3 main.py

run:
	cd src/ && python3 main.py

down:
	docker-compose down
