package scaletest;

import java.util.Properties;
import java.util.concurrent.CountDownLatch;
import org.apache.kafka.common.serialization.Serdes;
import org.apache.kafka.streams.KafkaStreams;
import org.apache.kafka.streams.StreamsBuilder;
import org.apache.kafka.streams.StreamsConfig;
import org.apache.kafka.streams.Topology;
import org.apache.kafka.streams.kstream.KStream;
import org.apache.log4j.Logger;

public class Pipe implements Runnable {
    public static void main(String[] args) throws Exception {
        Pipe pipe = new Pipe("minas-source", "minas-sink");
        final CountDownLatch latch = new CountDownLatch(1);
        // attach shutdown handler to catch control-c
        Runtime.getRuntime().addShutdownHook(new Thread("streams-shutdown-hook") {
            @Override
            public void run() {
                pipe.streams.close();
                latch.countDown();
            }
        });
        //
        try {
            pipe.streams.start();
            latch.await();
        } catch (Throwable e) {
            System.exit(1);
        }
        System.exit(0);
    }

    KafkaStreams streams;
    final Logger logger = Logger.getLogger(Pipe.class);

    public Pipe(String sourceTopic, String sinkTopic) {
        Properties props = new Properties();
        props.put(StreamsConfig.APPLICATION_ID_CONFIG, "streams-pipe");
        props.put(StreamsConfig.BOOTSTRAP_SERVERS_CONFIG, "localhost:9092");
        props.put(StreamsConfig.DEFAULT_KEY_SERDE_CLASS_CONFIG, Serdes.String().getClass());
        props.put(StreamsConfig.DEFAULT_VALUE_SERDE_CLASS_CONFIG, Serdes.String().getClass());
        //
        final StreamsBuilder builder = new StreamsBuilder();
        KStream<String, String> source = builder.stream("minas-source");
        source.to("minas-sink");
        //
        final Topology topology = builder.build();
        System.out.println(topology.describe());
        // 
        this.streams = new KafkaStreams(topology, props);
        logger.info("Pipe ready");
    }

    public synchronized void requestStop() {
        this.streams.close();
    }

    @Override
    public void run() {
        logger.info("Pipe running");
        this.streams.start();
    }
}
