package scaletest;

import org.apache.log4j.Logger;

import java.io.File;
import java.io.IOException;

public class ScaleTest {
    final String SOURCE = "minas-source";
    final String SINK = "minas-sink";
    final String CONTROL = "minas-control";
    final Logger logger = Logger.getLogger(ScaleTest.class);

    final String zookeeperCmd = "./kafka/bin/zookeeper-server-start.sh ./kafka.config/zookeeper.properties";
    final String kafkaBroker0Cmd = "./kafka/bin/kafka-server-start.sh ./kafka.config/servers/server.0.properties";
    SubProcess zookeeper;
    SubProcess kafka;
    int cores;
    String home;

    /**
     * Assumes:
     *  - pwd=/home/puhl/project/minas-py
     *  - dataDir=./run/kafka/tmp/zookeeper
     *  - ```sh
     *     sudo mount -t tmpfs -o size=1g tmpfs ~/project/minas-py/run/kafka/tmp
     *  ```
     *  - export MINAS_PY_HOME=$(pwd)
    */
    public static void main(String[] args) throws Exception {
        final String homeVar = "MINAS_PY_HOME";
        String home = System.getenv(homeVar);
        if (home == null) {
            throw new Exception("Environment '"+homeVar+"' is not set.");
        }
        home += File.separator;
        for (int cores = 1; cores < Runtime.getRuntime().availableProcessors(); cores++) {
            ScaleTest test = new ScaleTest(home, cores);
            Thread shutdownHook = new Thread(() -> {
                try {
                    test.tearDown();
                } catch (IOException | InterruptedException e) {
                    // pass
                }
            });
            Runtime.getRuntime().addShutdownHook(shutdownHook);
            try {
                test.setUp();
                test.run();
            } finally {
                test.tearDown();
            }
            Runtime.getRuntime().removeShutdownHook(shutdownHook);
        }
    }

    public ScaleTest(String home, int cores) {
        this.cores = cores;
        this.home = home;
    }

    public void setUp() throws Exception {
        zookeeper = new SubProcess("zookeeper", zookeeperCmd, ".+binding to port.+", home);
        zookeeper.run();
        //
        kafka = new SubProcess("kafka", kafkaBroker0Cmd, ".+started \\(kafka\\.server\\.KafkaServer.+", home);
        kafka.run();
    }

    public void tearDown() throws IOException, InterruptedException {
        long start = System.currentTimeMillis();
        kafka.tearDown();
        logger.info("Kafka teardown done in " + (System.currentTimeMillis() - start));
        //
        start = System.currentTimeMillis();
        zookeeper.tearDown();
        logger.info("Zookeeper teardown done in " + (System.currentTimeMillis() - start));
        // rm -rf ./tmp/*
        // dataDir=./run/kafka/tmp/zookeeper
        logger.info("Removing temp dir");
        Process rm = Runtime.getRuntime().exec("rm -rf ./run/kafka/tmp/*", null, new File(home));
        rm.getInputStream().transferTo(System.out);
        rm.waitFor();
        logger.info(rm.info());
    }

    public void run() {
        Pipe pipe = new Pipe(SOURCE, SINK, this.cores);
        Thread pipeThread = new Thread(pipe);

        TimerSink timerSink = new TimerSink(CONTROL, SINK);
        Thread timerThread = new Thread(timerSink);

        StressProducer stressProducer = new StressProducer(CONTROL, SINK);
        Thread producerThread = new Thread(stressProducer);

        try {
            pipeThread.start();
            timerThread.start();
            producerThread.start();

            producerThread.join();
            logger.info("Producer Joined");
            timerThread.join();
            logger.info("Timer Joined");
            pipe.requestStop();
            pipeThread.join();
            logger.info("Pipe Joined");
        } catch (InterruptedException e) {
            logger.info("Exception on join", e);
        }
    }
}
