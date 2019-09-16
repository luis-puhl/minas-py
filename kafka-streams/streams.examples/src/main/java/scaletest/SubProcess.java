package scaletest;

import org.apache.log4j.Logger;

import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.util.Scanner;
import java.util.concurrent.TimeUnit;

public
class SubProcess {
    private String name, cmd, flag;
    Process proc;
    private Thread shutdownHook;
    final Logger logger = Logger.getLogger(ScaleTest.class);
    private File pwd;

    public SubProcess(String name, String cmd, String flag, String dir) {
        this.name = name;
        this.cmd = cmd;
        this.flag = flag;
        this.pwd = new File(dir);
    }

    public void run() throws Exception {
        logger.info("Starting " + name);
        Runtime runtime = Runtime.getRuntime();
        proc = runtime.exec(cmd, null, pwd);
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
        if (!proc.waitFor(1, TimeUnit.SECONDS)) {
            runtime.exec("kill -SIGKILL " + proc.pid()).waitFor();
        }
        try {
            runtime.removeShutdownHook(shutdownHook);
        } catch (Exception e) {
            //
        }
    }

    private void waitForFlag(InputStream stream) throws Exception {
        long timeout = 100;
        Scanner pout = new Scanner(stream);
        long start = System.currentTimeMillis();
        while (true) {
            while (pout.hasNextLine()) {
                String line = pout.nextLine();
                int lineLen = Math.min(line.length(), 160);
                boolean found = line.matches(flag);
                System.out.println("---" + line.substring(0, lineLen) + (found ? " ***" : " ---"));
                if (found) {
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
