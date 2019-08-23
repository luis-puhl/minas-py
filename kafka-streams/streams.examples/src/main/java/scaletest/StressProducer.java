package scaletest;

import java.util.Properties;
import java.util.List;
import java.nio.file.Paths;
import java.nio.file.Files;

import org.apache.kafka.clients.producer.Producer;
import org.apache.kafka.clients.producer.KafkaProducer;
import org.apache.kafka.clients.producer.ProducerRecord;

public class StressProducer {
    public static void main(String[] args) throws Exception{
        String fileName = "/home/puhl/project/minas-py/kafka-streams/streams.examples/src/main/java/scaletest/KDDTe5Classes_cassales.csv";
        System.out.printf("Reading from %s\n", fileName);
        List<String> csvLines = Files.readAllLines(Paths.get(fileName));

        Properties props = new Properties();
        props.put("bootstrap.servers", "localhost:9092");
        props.put("acks", "all");
        props.put("retries", 0);
        props.put("batch.size", 16384);
        props.put("linger.ms", 1);
        props.put("buffer.memory", 33554432);
        props.put("key.serializer", "org.apache.kafka.common.serialization.StringSerializer");
        props.put("value.serializer", "org.apache.kafka.common.serialization.StringSerializer");

        Producer<String, String> producer = new KafkaProducer<>(props);

        long start = System.currentTimeMillis();
        int iter = 0;
        for (String line: csvLines) {
            producer.send(new ProducerRecord<String, String>("minas-source", line));
            iter++;
        }
        long elapsedTimeMillis = System.currentTimeMillis() - start;
        System.out.printf("Time taken: %d ms. Sent instances: %d.\n", elapsedTimeMillis, iter);
        System.out.println("Message sent successfully");
        producer.close();
    }
}
