FROM decodeproject/chainspace-java:SNAPSHOT

# The contracts in asonino are designed to be placed inside the chainspace examples.

WORKDIR /app/coconut-contracts

COPY contracts contracts
COPY tests tests
COPY run_tests.sh .
COPY run_petition.sh .
COPY run_petition.py .


CMD ./run_tests.sh


