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
    boolean runningFlag = false;
    final Logger logger = Logger.getLogger(Pipe.class);
    
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
        System.out.printf("Consumer Ready\n");
        System.out.flush();
    }
    
    @Override
    public void run() {
        final int giveUp = 10;
        int noRecordsCount = 0;

        while (true) {
            final ConsumerRecords<String, String> consumerRecords = this.consumer.poll(Duration.ofSeconds(1));

            if (consumerRecords.count() == 0) {
                System.out.printf("Pool with zero records\n");
                noRecordsCount++;
                if (noRecordsCount > giveUp) break;
                else continue;
            }
            for (ConsumerRecord<String, String> record: consumerRecords) {
                this.consume(record);
                if (runningFlag && this.sinkConuter <= 0) {
                    break;
                }
            }

            this.consumer.commitAsync();
            System.out.flush();
        }
        this.consumer.close();
        System.out.printf("DONE\n");
    }
    
    void consume(ConsumerRecord<String, String> record) {
        if ( this.controlTopic.equals(record.topic()) ) {
            if (this.runningFlag) {
                this.sinkConuter = Integer.getInteger(record.value());
                System.out.printf("%d sink counter update.\n", this.sinkConuter);
            }
            this.runningFlag = true;
        } else if (this.runningFlag) {
            this.sinkConuter--;
        } else {
            System.out.printf("Consumer Record:(%s, %s, %s, %d, %d)\n", record.topic(), record.key(), record.value(), record.partition(), record.offset());
        }
    }
}
