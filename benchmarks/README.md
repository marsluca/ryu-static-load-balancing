# Benchmarks

## Throughput test:
#### Client:
	sudo ./throughput.sh <CLIENT_NAME> <SERVER_IP>
Example:
	sudo ./throughput.sh H1 10.0.1.100
#### Server:
	netserver &

## Requests distribution test:
#### Client:
	./requests_distribution_server.sh <CLIENT_NAME> <SERVER_IP> <REQUEST_NUMBER>
Example:
	./requests_distribution_server.sh H2 10.0.1.100 100
#### Server:
	./requests_distribution_server.sh <SERVER_NAME>
Example:
	./requests_distribution_server.sh H1
