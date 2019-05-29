#!/bin/bash
./kafka/bin/zookeeper-server-start.sh kafka.config/zookeeper.properties &
sleep 10

./kafka/bin/kafka-server-start.sh kafka.config/servers/server.0.properties &
./kafka/bin/kafka-server-start.sh kafka.config/servers/server.1.properties &
./kafka/bin/kafka-server-start.sh kafka.config/servers/server.2.properties &
sleep 10

./kafka/bin/kafka-topics.sh --create --zookeeper localhost:2181 --replication-factor 1 --partitions 16 --topic minas-topic
# ./bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic minas-topic --from-beginning
export ZK_HOSTS="localhost:2181"
./kafka-manager/bin/kafka-manager
