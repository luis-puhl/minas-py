package scaletest;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.List;
import java.util.Properties;
import org.apache.log4j.Logger;
import org.apache.kafka.clients.producer.ProducerConfig;
import org.apache.kafka.clients.producer.KafkaProducer;
import org.apache.kafka.clients.producer.Producer;
import org.apache.kafka.clients.producer.ProducerRecord;
import org.apache.kafka.common.serialization.StringSerializer;

public class StressProducer implements Runnable {
    public static void main(String[] args) throws Exception {
        StressProducer stressProducer = new StressProducer("minas-control", "minas-source");
        stressProducer.run();
    }

    long start;
    String controlTopic;
    String sourceTopic;
    final Logger logger = Logger.getLogger(StressProducer.class);

    public StressProducer(String controlTopic, String sourceTopic) {
        this.controlTopic = controlTopic;
        this.sourceTopic = sourceTopic;
        this.start = System.currentTimeMillis();
        logger.info(String.format("t0 = %d", this.start));
    }

    void printTime(String message, Object... args) {
        String prefix = String.format("[%d] ", System.currentTimeMillis() - this.start);
        logger.info(String.format(prefix + message, args));
        this.start = System.currentTimeMillis();
    }

    @Override
    public void run() {
        String fileName = "./tmp/KDDTe5Classes_cassales.csv";
        logger.info(String.format("Reading from %s", fileName));
        List<String> csvLines;
        try {
            csvLines = Files.readAllLines(Paths.get(fileName));
        } catch (IOException ex) {
            logger.fatal(null, ex);
            return;
        }
        int recordCount = csvLines.size();
        this.printTime("Reading complete.");

        Properties props = new Properties();
        props.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, "localhost:9092");
        props.put(ProducerConfig.ACKS_CONFIG, "all");
        props.put(ProducerConfig.RETRIES_CONFIG, 0);
        props.put(ProducerConfig.BATCH_SIZE_CONFIG, 16384);
        props.put(ProducerConfig.LINGER_MS_CONFIG, 1);
        props.put(ProducerConfig.BUFFER_MEMORY_CONFIG, 33554432);
        props.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG, StringSerializer.class.getName());
        props.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, StringSerializer.class.getName());

        Producer<String, String> producer = new KafkaProducer<>(props);
        producer.send(new ProducerRecord<String, String>(this.controlTopic, String.format("producing_load =%d", recordCount)));
        this.printTime("Producer ready.");

        int keyIndex = 0;
        for (String line: csvLines) {
            producer.send(new ProducerRecord<>(this.sourceTopic, String.format("%d", keyIndex), line));
            keyIndex++;
        }
        producer.flush();
        this.printTime("All %d records sent.", recordCount);

        producer.close();
    }

}
