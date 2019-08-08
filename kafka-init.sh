#!/bin/bash

# RAM DISK
# mkdir /tmp/kafka
# mount -t tmpfs -o size=512m tmpfs /tmp/kafka

./kafka/bin/zookeeper-server-start.sh kafka.config/zookeeper.properties &
pids[${i}]=$!
sleep 10

./kafka/bin/kafka-server-start.sh kafka.config/servers/server.0.properties &
pids[${i}]=$!
./kafka/bin/kafka-server-start.sh kafka.config/servers/server.1.properties &
pids[${i}]=$!
./kafka/bin/kafka-server-start.sh kafka.config/servers/server.2.properties &
pids[${i}]=$!
sleep 10

./kafka/bin/kafka-topics.sh --zookeeper localhost:2181 --topic items --create --if-not-exists --replication-factor 1 --partitions 8 &
pids[${i}]=$!
./kafka/bin/kafka-topics.sh --zookeeper localhost:2181 --topic clusters --create --if-not-exists --replication-factor 1 --partitions 8 &
pids[${i}]=$!
./kafka/bin/kafka-topics.sh --zookeeper localhost:2181 --topic numbers --create --if-not-exists --replication-factor 1 --partitions 8 &
pids[${i}]=$!

# wait for all pids
for pid in ${pids[*]}; do
    sleep 10
    wait $pid
done

for job in `jobs -p`
do
    echo $job
    wait $job || echo "FAIL $job"
done

# ./bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic minas-topic --from-beginning
# export ZK_HOSTS="localhost:2181"
# ./kafka-manager/bin/kafka-manager
