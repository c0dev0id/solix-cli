VENV    := .venv
PYTHON  := $(VENV)/bin/python3
PIP     := $(VENV)/bin/pip

INSTALL_DIR := $(HOME)/python

.PHONY: all venv install update clean

all: venv

$(VENV)/bin/python3:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install aiohttp aiofiles cryptography "paho-mqtt>=2.1.0" python-dotenv click
	$(PIP) install -e vendor/anker-solix-api
	$(PIP) install -e .

venv: $(VENV)/bin/python3

install: $(VENV)/bin/python3
	python3 -m pip install --prefix=$(INSTALL_DIR) vendor/anker-solix-api .

update:
	git submodule update --remote vendor/anker-solix-api
	$(PIP) install -e vendor/anker-solix-api

clean:
	rm -rf $(VENV)
