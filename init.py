import subprocess
import shlex
import signal
from multiprocessing import Process

import minas.sys_monitor as sys_monitor

processes = []
def exit_gracefully(signum, frame):
    print('killed', signum, processes)
    for p in processes:
        if hasattr(p, 'terminate'):
            p.terminate()
        if hasattr(p, 'kill'):
            p.kill()
    exit()
signal.signal(signal.SIGINT, exit_gracefully)
signal.signal(signal.SIGTERM, exit_gracefully)
# signal.signal(signal.SIGKILL, exit_gracefully)
signal.signal(signal.SIGQUIT, exit_gracefully)

sys_monitor_cmd = 'python ./minas/sys_monitor.py'
sys_monitor_ready_flag = 'SYSTEM MONITOR READY'

zookeeper_cmd = './kafka/bin/zookeeper-server-start.sh kafka.config/zookeeper.properties'
zookeeper_ready_flag = 'INFO binding to port'

kafka_cluster_0 = './kafka/bin/kafka-server-start.sh kafka.config/servers/server.0.properties'
kafka_cluster_1 = './kafka/bin/kafka-server-start.sh kafka.config/servers/server.1.properties'
kafka_cluster_2 = './kafka/bin/kafka-server-start.sh kafka.config/servers/server.2.properties'
kafka_ready_flag = 'started (kafka.server.KafkaServer)'

topic_items = './kafka/bin/kafka-topics.sh --zookeeper localhost:2181 --topic items --create --replication-factor 1 --partitions 8'
topic_clusters = './kafka/bin/kafka-topics.sh --zookeeper localhost:2181 --topic clusters --create --replication-factor 1 --partitions 8'
topic_numbers = './kafka/bin/kafka-topics.sh --zookeeper localhost:2181 --topic numbers --create --replication-factor 1 --partitions 8'

def mk_proc(cmd, ready_flag):
    args = shlex.split(cmd)
    process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
    processes.append(process)
    while process.stdout.readable():
        line = process.stdout.readline()
        print(str(line).replace('\n', ''))
        if ready_flag in line:
            break
    return process

# sys_monitor_process = mk_proc(sys_monitor_cmd, sys_monitor_ready_flag)
sys_monitor_process = Process(target=sys_monitor, name='sys_monitor')
processes.append(sys_monitor_process)
sys_monitor_process.start()

zookeeper_process = mk_proc(zookeeper_cmd, zookeeper_ready_flag)
kafka_process = mk_proc(kafka_cluster_0, kafka_ready_flag)

kafka_process.terminate()
zookeeper_process.terminate()
sys_monitor_process.terminate()
