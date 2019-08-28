package scaletest;

import org.apache.log4j.Logger;

public class ScaleTest {
    public static void main(String[] args) {
        final String SOURCE = "minas-source";
        final String SINK = "minas-sink";
        final String CONTROL = "minas-control";
        final Logger logger = Logger.getLogger(ScaleTest.class);
        
        Pipe pipe = new Pipe(SOURCE, SINK);
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
