package scaletest;

import java.time.Duration;
import java.util.ArrayList;
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
    long sinkConuter = 0;
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
        while (true) {
            final ConsumerRecords<String, String> consumerRecords = this.consumer.poll(Duration.ofSeconds(5));
            if (consumerRecords.count() == 0) {
                logger.info("Pool with zero records");
                break;
            }
            for (ConsumerRecord<String, String> record: consumerRecords) {
                this.msgCount++;
                this.consume(record);
                if (this.runningFlag && this.sinkConuter <= 0) {
                    break;
                }
            }
            this.consumer.commitAsync();
        }
        this.consumer.close();
        this.consumer.unsubscribe();
        logger.info(String.format("DONE, %d, msgCount=%d", this.sinkConuter, this.msgCount));
    }
    
    void consume(ConsumerRecord<String, String> record) {
        if ( this.controlTopic.equals(record.topic()) ) {
            try {
                String sourceNumber = record.value();
                this.sinkConuter = Integer.decode(sourceNumber.split("=")[1]);
                logger.info(String.format("[%d] sink counter update.", this.sinkConuter));
            } catch (NumberFormatException e) {
                // pass
            } finally {
                this.runningFlag = true;
            }
        } else if (this.runningFlag && this.sinkTopic.equals(record.topic())) {
            this.sinkConuter--;
            return;
        }
        String message = "Consumer Record:(%s, %s, %s, %d, %d)";
        message = String.format(message, record.topic(), record.key(), record.value(), record.partition(), record.offset());
        logger.info(message);
    }
}
