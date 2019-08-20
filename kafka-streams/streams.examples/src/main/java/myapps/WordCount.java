package myapps;

import java.util.Arrays;
import java.util.Locale;
import org.apache.kafka.common.serialization.Serdes;
import org.apache.kafka.streams.KafkaStreams;
import org.apache.kafka.streams.StreamsBuilder;
import org.apache.kafka.streams.StreamsConfig;
import org.apache.kafka.streams.Topology;

import java.util.Properties;
import java.util.concurrent.CountDownLatch;
import org.apache.kafka.common.utils.Bytes;
import org.apache.kafka.streams.kstream.KGroupedStream;
import org.apache.kafka.streams.kstream.KStream;
import org.apache.kafka.streams.kstream.KTable;
import org.apache.kafka.streams.kstream.KeyValueMapper;
import org.apache.kafka.streams.kstream.Materialized;
import org.apache.kafka.streams.kstream.Produced;
import org.apache.kafka.streams.kstream.ValueMapper;
import org.apache.kafka.streams.state.KeyValueStore;

public class WordCount {
    public static void main(String[] args) throws Exception {
        int cores = Runtime.getRuntime().availableProcessors();
        
        Properties props = new Properties();
        props.put(StreamsConfig.APPLICATION_ID_CONFIG, "streams-wordcount");
        props.put(StreamsConfig.BOOTSTRAP_SERVERS_CONFIG, "localhost:9092");
        props.put(StreamsConfig.DEFAULT_KEY_SERDE_CLASS_CONFIG, Serdes.String().getClass());
        props.put(StreamsConfig.DEFAULT_VALUE_SERDE_CLASS_CONFIG, Serdes.String().getClass());
        props.put(StreamsConfig.NUM_STREAM_THREADS_CONFIG, cores);
        //
        final StreamsBuilder builder = new StreamsBuilder();
        KStream<String, String> source = builder.stream("streams-plaintext-input");
        Locale locale = Locale.getDefault();
        KStream<String, String> words = source.flatMapValues(
                value -> Arrays.asList(value.toLowerCase(locale).split("\\W+"))
        );
        KGroupedStream<String, String> wordsGrouped = words.groupBy(
                (key, value) -> value
        );
        // Materialize the result into a KeyValueStore named "counts-store".
        // The Materialized store is always of type <Bytes, byte[]> as this is the format of the inner most store.
        Materialized<String, Long, KeyValueStore<Bytes, byte[]>> materialized;
        materialized = Materialized.<String, Long, KeyValueStore<Bytes, byte[]>> as("counts-store");
        KTable<String, Long> count = wordsGrouped.count(materialized);
        count.toStream().to("streams-wordcount-output", Produced.with(Serdes.String(), Serdes.Long()));
        /*
        KStream<String, String> words = source.flatMapValues(new ValueMapper<String, Iterable<String>>() {
            @Override
            public Iterable<String> apply(String value) {
                value = value.toLowerCase(locale);
                return Arrays.asList(value.split("\\W+"));
            }
        });
        */
        /*
        words.groupBy(new KeyValueMapper<String, String, String>() {
        @Override
        public Object apply(String key, String value) {
        return value;
        }
        });
         */
        //
        final Topology topology = builder.build();
        System.out.println(topology.describe());
        // 
        final KafkaStreams streams = new KafkaStreams(topology, props);
        //
        final CountDownLatch latch = new CountDownLatch(1);
        // attach shutdown handler to catch control-c
        Runtime.getRuntime().addShutdownHook(new Thread("streams-shutdown-hook") {
            @Override
            public void run() {
                streams.close();
                latch.countDown();
            }
        });
        //
        try {
            streams.start();
            latch.await();
        } catch (Throwable e) {
            System.exit(1);
        }
        System.exit(0);
    }
}
