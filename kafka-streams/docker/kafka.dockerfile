FROM confluentinc/cp-kafka

ENV LOG_DIRS=/var/lib/kafka

RUN mkdir $LOG_DIRS ; \
    mount -t tmpfs -o size=1g tmpfs $LOG_DIRS

