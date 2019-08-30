package scaletest;

import org.apache.log4j.Logger;

import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.util.Scanner;

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
            test.setUp();
            test.run();
            test.tearDown();
        }
    }

    public ScaleTest(String home, int cores) {
        this.cores = cores;
        this.home = home;
    }

    public void setUp() throws Exception {
        zookeeper = new SubProcess("zookeeper", zookeeperCmd.replaceAll("\\.\\/", home), ".+binding to port.+");
        zookeeper.run();
        //
        kafka = new SubProcess("kafka", kafkaBroker0Cmd.replaceAll("\\.\\/", home), "started (kafka.server.KafkaServer");
        kafka.run();
    }

    public void tearDown() throws IOException, InterruptedException {
        kafka.tearDown();
        zookeeper.tearDown();
        // rm -rf ./tmp/*
        // dataDir=./run/kafka/tmp/zookeeper
        Process rm = Runtime.getRuntime().exec("rm -rf ./run/kafka/tmp/*".replace("\\.\\/", home));
        rm.getInputStream().transferTo(System.out);
        rm.waitFor();
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

class SubProcess {
    private String name, cmd, flag;
    Process proc;
    private Thread shutdownHook;
    final Logger logger = Logger.getLogger(ScaleTest.class);

    public SubProcess(String name, String cmd, String flag) {
        this.name = name;
        this.cmd = cmd;
        this.flag = flag;
    }

    public void run() throws Exception {
        logger.info("Starting " + name);
        Runtime runtime = Runtime.getRuntime();
        proc = runtime.exec(cmd);
        shutdownHook = new Thread(() -> {
            logger.info("Shutting down "+ name);
            try {
                runtime.exec("kill -SIGINT " + proc.pid()).waitFor();
            } catch (IOException | InterruptedException e) {
                proc.destroyForcibly();
            }
        });
        runtime.addShutdownHook(shutdownHook);
        waitForFlag(proc.getInputStream());
        logger.info(name + " Ready");
    }

    public void tearDown() throws IOException, InterruptedException {
        Runtime runtime = Runtime.getRuntime();
        runtime.exec("kill -SIGINT " + proc.pid()).waitFor();
        proc.waitFor();
        runtime.removeShutdownHook(shutdownHook);
    }

    private void waitForFlag(InputStream stream) throws Exception {
        long timeout = 100;
        Scanner pout = new Scanner(stream);
        long start = System.currentTimeMillis();
        while (true) {
            System.out.print(".");
            while (pout.hasNextLine()) {
                String line = pout.nextLine();
                System.out.println("---" +line.substring(0, 80) + "   " + line.matches(flag));
                if (line.matches(flag)) {
                    return;
                }
            }
            try {
                Thread.sleep(10);
            } catch (InterruptedException e) {
                // pass
            }
            if ((System.currentTimeMillis() - start) > timeout) {
                throw new Exception("Timeout on process '"+name+"'start.");
            }
        }
    }
}