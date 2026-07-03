VENV    := .venv
PYTHON  := $(VENV)/bin/python3
PIP     := $(VENV)/bin/pip

INSTALL_VENV := $(HOME)/.local/lib/solix-cli
BIN_LINK     := $(HOME)/bin/solix-cli
MAN_DIR      := $(HOME)/.local/share/man/man1

.PHONY: all venv install update clean

all: venv

$(VENV)/bin/python3:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(PIP) install -e vendor/anker-solix-api
	$(PIP) install -e .

venv: $(VENV)/bin/python3

install:
	python3 -m venv $(INSTALL_VENV)
	$(INSTALL_VENV)/bin/pip install --upgrade pip
	$(INSTALL_VENV)/bin/pip install vendor/anker-solix-api .
	mkdir -p $(HOME)/bin
	ln -sf $(INSTALL_VENV)/bin/solix-cli $(BIN_LINK)
	mkdir -p $(MAN_DIR)
	install -m 644 solix-cli.1 $(MAN_DIR)/solix-cli.1

update:
	git submodule update --remote vendor/anker-solix-api
	$(PIP) install -e vendor/anker-solix-api

clean:
	rm -rf $(VENV) build/ src/*.egg-info
