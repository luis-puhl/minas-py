import subprocess
import shlex
import signal
from multiprocessing import Process
from multiprocessing import cpu_count
import os

import minas.sys_monitor as sys_monitor

processes = []
def terminate():
    while len(processes) > 0:
        for p in reversed(processes):
            print('terminating', p.args[0])
            return_code = p.poll()
            if hasattr(p, 'poll') and return_code is not None:
                print('poll =>', return_code)
                processes.remove(p)
                continue
            if hasattr(p, 'send_signal'):
                print('send_signal')
                p.send_signal(signal.SIGINT)
            elif hasattr(p, 'terminate'):
                print('terminate')
                p.terminate()
            elif hasattr(p, 'kill'):
                print('kill')
                p.kill()
            try:
                print('wait')
                # return_code = p.wait(1)
                p.communicate(timeout=1)
                return_code = p.returncode
                processes.remove(p)
                print('returned ', return_code)
            except:
                print('waited, no return')
def exit_gracefully(signum, frame):
    print('killed', signum, processes)
    terminate()
    exit()
signal.signal(signal.SIGINT, exit_gracefully)
signal.signal(signal.SIGTERM, exit_gracefully)
# signal.signal(signal.SIGKILL, exit_gracefully)
signal.signal(signal.SIGQUIT, exit_gracefully)

sys_monitor_cmd = 'python ./minas/sys_monitor.py'
sys_monitor_ready_flag = 'SYSTEM MONITOR READY'

zookeeper_cmd = './kafka/bin/zookeeper-server-start.sh ./kafka.config/zookeeper.properties'
zookeeper_ready_flag = 'INFO binding to port'

kafka_cluster_0 = './kafka/bin/kafka-server-start.sh ./kafka.config/servers/server.0.properties'
kafka_cluster_1 = './kafka/bin/kafka-server-start.sh ./kafka.config/servers/server.1.properties'
kafka_cluster_2 = './kafka/bin/kafka-server-start.sh ./kafka.config/servers/server.2.properties'
kafka_ready_flag = 'started (kafka.server.KafkaServer)'

topics = [ 'items', 'clusters', 'numbers', ]
create_topic = './kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --topic {topic} --create --if-not-exists --replication-factor 1 --partitions {cores}'

def mk_proc(cmd, ready_flag, fail_flag=''):
    if type(cmd) is not list:
        args = shlex.split(cmd)
    else:
        args = cmd
    print(args, 'wait for', ready_flag)
    process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8', env=os.environ, cwd=os.getcwd())
    processes.append(process)
    while process.stdout.readable():
        line = str(process.stdout.readline()).strip()
        if len(line) > 0:
            print(line.replace('\n', ''))
        if ready_flag in line:
            print('ready')
            break
        if len(fail_flag) > 1 and fail_flag in line:
            print('fail')
            raise Exception('Failed to be ready')
    return process
# 

if __name__ == "__main__":
    try:
        sys_monitor_process = mk_proc(sys_monitor_cmd, sys_monitor_ready_flag)
        
        zookeeper_process = mk_proc(zookeeper_cmd, zookeeper_ready_flag, fail_flag='USAGE')
        kafka_process = mk_proc(kafka_cluster_0, kafka_ready_flag, fail_flag='USAGE')
        
        cores = str(cpu_count())
        for topic in topics:
            cmd = shlex.split(create_topic.format(cores=cores, topic=topic))
            mk_proc(cmd, '')
    finally:
        terminate()
