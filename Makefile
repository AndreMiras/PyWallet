VIRTUAL_ENV ?= venv
ACTIVATE_PATH=$(VIRTUAL_ENV)/bin/activate
PIP=$(VIRTUAL_ENV)/bin/pip
PYTHON_MAJOR_VERSION=3
PYTHON_MINOR_VERSION=7
PYTHON_VERSION=$(PYTHON_MAJOR_VERSION).$(PYTHON_MINOR_VERSION)
PYTHON_MAJOR_MINOR=$(PYTHON_MAJOR_VERSION)$(PYTHON_MINOR_VERSION)
PYTHON_WITH_VERSION=python$(PYTHON_VERSION)
PYTHON=$(VIRTUAL_ENV)/bin/python
ISORT=$(VIRTUAL_ENV)/bin/isort
FLAKE8=$(VIRTUAL_ENV)/bin/flake8
PYTEST=$(VIRTUAL_ENV)/bin/pytest
COVERAGE=$(VIRTUAL_ENV)/bin/coverage
TWINE=`which twine`
SOURCES=src/
DOCKER_IMAGE_LINUX=andremiras/pywallet-linux
DOCKER_IMAGE_ANDROID=andremiras/pywallet-android
DOCKER_VOLUME=/tmp/.X11-unix:/tmp/.X11-unix
SYSTEM_DEPENDENCIES_BASE= \
    libpython$(PYTHON_VERSION)-dev \
    python$(PYTHON_VERSION)
SYSTEM_DEPENDENCIES_LINUX= \
    build-essential \
    libgl1 \
    libzbar0 \
    python$(PYTHON_MAJOR_VERSION)-virtualenv \
    tox
SYSTEM_DEPENDENCIES_ANDROID= \
    autoconf \
    automake \
    cmake \
    gettext \
    libffi-dev \
    libltdl-dev \
    git \
    libssl-dev \
    libtool \
    openjdk-8-jdk-headless \
    patch \
    pkg-config \
    python$(PYTHON_MAJOR_VERSION)-pip \
    python$(PYTHON_MAJOR_VERSION)-setuptools \
    unzip \
    zlib1g-dev \
    zip
ifndef CI
DOCKER_DEVICE=--device=/dev/video0:/dev/video0
DOCKER_IT=-it
endif

all: virtualenv

system_dependencies:
	apt update -qq > /dev/null && sudo apt -qq install --yes --no-install-recommends $(SYSTEM_DEPENDENCIES_BASE)

system_dependencies/linux: system_dependencies
	apt update -qq > /dev/null && sudo apt -qq install --yes --no-install-recommends $(SYSTEM_DEPENDENCIES_LINUX)

system_dependencies/android: system_dependencies
	apt update -qq > /dev/null && sudo apt -qq install --yes --no-install-recommends $(SYSTEM_DEPENDENCIES_ANDROID)

$(VIRTUAL_ENV):
	virtualenv --python $(PYTHON_WITH_VERSION) $(VIRTUAL_ENV)
	$(PIP) install Cython==0.28.6
	$(PIP) install -r requirements.txt

virtualenv: $(VIRTUAL_ENV)

run: virtualenv
	$(PYTHON) src/main.py

pytest: virtualenv
	$(COVERAGE) erase
	$(COVERAGE) run -m unittest discover --start-directory=src/
	$(COVERAGE) report

test: pytest lint
	@if test -n "$$CI"; then make uitest; fi; \

uitest:
	. $(ACTIVATE_PATH) && \
	$(PYTHON) -m kivyunittest --folder src/tests/ui/ --pythonpath src/

lint/isort-check: virtualenv
	$(ISORT) --check-only --recursive --diff $(SOURCES)

lint/isort-fix: virtualenv
	$(ISORT) --recursive $(SOURCES)

lint/flake8: virtualenv
	$(FLAKE8) $(SOURCES)

lint/mypy: virtualenv
	# $(MYPY) --ignore-missing-imports $(shell find src/pywallet/ -name "*.py")

lint: lint/isort-check lint/flake8 lint/mypy

release/clean:
	rm -rf dist/ build/

release/build: release/clean clean
	$(PYTHON) setup.py sdist bdist_wheel
	$(TWINE) check dist/*

release/upload:
	$(TWINE) upload dist/*

clean:
	rm -rf .pytest_cache/
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type d -name "*.egg-info" -exec rm -r {} +

clean/venv: clean
	rm -rf $(VIRTUAL_ENV)

buildozer/android/debug:
	@if test -n "$$CI"; then sed 's/log_level = [0-9]/log_level = 1/' -i buildozer.spec; fi; \
	buildozer android debug

docker/pull/linux:
	docker pull $(DOCKER_IMAGE_LINUX):latest

docker/pull/android:
	docker pull $(DOCKER_IMAGE_ANDROID):latest

docker/build/linux:
	docker build --cache-from=$(DOCKER_IMAGE_LINUX) --tag=$(DOCKER_IMAGE_LINUX) --file=dockerfiles/Dockerfile-linux .

docker/build/android:
	docker build --cache-from=$(DOCKER_IMAGE_ANDROID) --tag=$(DOCKER_IMAGE_ANDROID) --file=dockerfiles/Dockerfile-android .

docker/push/linux:
	docker push $(DOCKER_IMAGE_LINUX)

docker/push/android:
	docker push $(DOCKER_IMAGE_ANDROID)

docker/push: docker/push/linux docker/push/android

docker/run/test/linux:
	docker run --env-file dockerfiles/env.list -v $(DOCKER_VOLUME) $(DOCKER_DEVICE) $(DOCKER_IT) --rm $(DOCKER_IMAGE_LINUX) make test

docker/run/test/android:
	docker run --env-file dockerfiles/env.list $(DOCKER_IMAGE_ANDROID) make buildozer/android/debug

docker/run/app:
	docker run --env-file dockerfiles/env.list -v $(DOCKER_VOLUME) $(DOCKER_DEVICE) -it --rm $(DOCKER_IMAGE_LINUX) make run

docker/run/shell/linux:
	docker run --env-file dockerfiles/env.list -v $(DOCKER_VOLUME) $(DOCKER_DEVICE) -it --rm $(DOCKER_IMAGE_LINUX)

docker/run/shell/android:
	docker run --env-file dockerfiles/env.list -v $(DOCKER_VOLUME) $(DOCKER_DEVICE) -it --rm $(DOCKER_IMAGE_ANDROID)
