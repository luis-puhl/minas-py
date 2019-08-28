package scaletest;

import java.time.Duration;
import java.util.ArrayList;
import java.util.LinkedList;
import java.util.List;
import java.util.Properties;
import org.apache.kafka.clients.consumer.Consumer;
import org.apache.kafka.clients.consumer.ConsumerConfig;
import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.apache.kafka.clients.consumer.ConsumerRecords;
import org.apache.kafka.clients.consumer.KafkaConsumer;
import org.apache.kafka.common.serialization.StringDeserializer;
import org.apache.log4j.Logger;

public class TimerSink implements Runnable {
    public static void main(String[] args) throws InterruptedException {
        TimerSink timerSink = new TimerSink("minas-control", "minas-sink");
        timerSink.run();
    }
    
    String controlTopic;
    String sinkTopic;
    Consumer<String, String> consumer;
    long sinkConuter = 1;
    long msgCount = 0;
    boolean runningFlag = false;
    Logger logger = Logger.getLogger(TimerSink.class);
    
    public TimerSink(String controlTopic, String sinkTopic) {
        this.controlTopic = controlTopic;
        this.sinkTopic = sinkTopic;
        List<String> topics = new ArrayList<>(2);
        topics.add(controlTopic);
        topics.add(sinkTopic);
        
        Properties props = new Properties();
        props.put(ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG, "localhost:9092");
        props.put(ConsumerConfig.GROUP_ID_CONFIG, "TimerSink");
        props.put(ConsumerConfig.KEY_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class.getName());
        props.put(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class.getName());
        this.consumer = new KafkaConsumer<>(props);
        
        this.consumer.subscribe(topics);
        logger.info("Consumer Ready");
    }
    
    @Override
    public void run() {
        logger = Logger.getLogger(TimerSink.class);
        logger.info("TimerSink running");
        List<ConsumerRecord<String, String>> buffer = new LinkedList<>();
        while (this.msgCount == 0  || this.sinkConuter > 0) {
            final ConsumerRecords<String, String> consumerRecords = this.consumer.poll(Duration.ofSeconds(5));
            if (consumerRecords.count() == 0) {
                logger.info("Pool with zero records");
                break;
            }
            for (ConsumerRecord<String, String> record: consumerRecords) {
                this.msgCount++;
                if (!this.runningFlag) {
                    if ( this.controlTopic.equals(record.topic()) ) {
                        try {
                            String sourceNumber = record.value();
                            this.sinkConuter = Integer.decode(sourceNumber.split("=")[1]);
                            logger.info(String.format("[%d] sink counter update.", this.sinkConuter));
                            this.runningFlag = true;
                        } catch (NumberFormatException e) {
                            // pass
                        }
                    } else if (this.sinkTopic.equals(record.topic())) {
                        buffer.add(record);
                    } else {
                        String message = "Consumer Record:(%s, %s, %s, %d, %d)";
                        message = String.format(message, record.topic(), record.key(), record.value(), record.partition(), record.offset());
                        logger.info(message);
                    }
                } else if (this.sinkTopic.equals(record.topic())) {
                    this.sinkConuter--;
                    if (buffer.size() > 0) {
                        for (ConsumerRecord<String, String> buffRecord: buffer) {
                            if (this.sinkTopic.equals(record.topic())) {
                                this.sinkConuter--;
                            }
                        }
                    }
                } else {
                    String message = "Consumer Record:(%s, %s, %s, %d, %d)";
                    message = String.format(message, record.topic(), record.key(), record.value(), record.partition(), record.offset());
                    logger.info(message);
                }
            }
            this.consumer.commitAsync();
        }
        this.consumer.unsubscribe();
        this.consumer.close();
        logger.info(String.format("DONE, %d, msgCount=%d", this.sinkConuter, this.msgCount));
    }
}
