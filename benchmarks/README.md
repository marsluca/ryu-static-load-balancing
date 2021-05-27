# Benchmarks

## Throughput test:
#### Client:
	sudo ./throughput_client.sh <CLIENT_NAME> <SERVER_IP>
Example:
	sudo ./throughput_client.sh H1 10.0.1.100
#### Server:
	sudo ./throughput_server.sh <SERVER_NAME>
Example:
	sudo ./throughput_server.sh SRV1

## Requests distribution test:
#### Client:
	./requests_distribution_client.sh <CLIENT_NAME> <SERVER_IP> <REQUEST_NUMBER>
Example:
	./requests_distribution_client.sh H2 10.0.1.100 100
#### Server:
	./requests_distribution_server.sh <SERVER_NAME>
Example:
	./requests_distribution_server.sh H1
