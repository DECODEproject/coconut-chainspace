# Makes a docker image with the system tests in it

build-docker:
	docker build -t decodeproject/chainspace-java-coconut-py-test:SNAPSHOT .

bash-docker:
	docker run -t -i decodeproject/chainspace-java-coconut-py-test:SNAPSHOT /bin/bash

# To connect it to an existing network try:
# docker network connect [OPTIONS] NETWORK CONTAINER
