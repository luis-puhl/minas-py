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
        System.out.printf("t0 = %d\n", this.start);
    }

    void printTime(String message, Object... args) {
        message = "[%d] " + message + "\n";
        Object[] moreArgs = new Object[args.length + 1];
        moreArgs[0] = System.currentTimeMillis() - this.start;
        if (args.length > 0) {
            System.arraycopy(args, 0, moreArgs, 1, args.length);
        }
        System.out.printf(message, moreArgs);
        this.start = System.currentTimeMillis();
    }

    @Override
    public void run() {
        String fileName = "/home/puhl/project/minas-py/kafka-streams/streams.examples/src/main/java/scaletest/KDDTe5Classes_cassales.csv";
        System.out.printf("Reading from %s\n", fileName);
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
        producer.send(new ProducerRecord<String, String>(this.controlTopic, "producing_load"));
        producer.send(new ProducerRecord<String, String>(this.controlTopic, String.format("%d", recordCount)));
        this.printTime("Producer ready.");

        for (String line : csvLines) {
            producer.send(new ProducerRecord<>(this.sourceTopic, line));
        }
        this.printTime("All %d records sent.", recordCount);

        producer.close();
    }

}