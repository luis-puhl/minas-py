import logging

import psutil
import matplotlib.pyplot as plt

log = logging.getLogger(__name__)
log.info(__name__)

stats = {}
def push(stats, key, value):
    if key not in stats:
        stats[key] = list()
    stats[key].append(value)
# 
cpu_stats_init = psutil.cpu_stats()
io_init = psutil.disk_io_counters(perdisk=True)

for i in range(10):
    for device, cores in psutil.sensors_temperatures().items():
        for shwtemp in cores:
            label, current, high, critical = shwtemp
            push(stats, f'temp {device} {label}', current)
    # 
    total, available, percent, used, free, active, inactive, buffers, cached, shared, slab = psutil.virtual_memory()
    push(stats, f'ram percent', percent)
    push(stats, f'ram used GB', used / 10**9 )
    # 
    current, _min, _max = psutil.cpu_freq()
    push(stats, f'cpu freq GHz', current / 10**3)
    # 
    cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
    for i, core_uesed in enumerate(cpu_percent):
        push(stats, f'cpu percent {i}', core_uesed)
    # 
    io = psutil.disk_io_counters(perdisk=True)
    for disk, io_stat_curr in io.items():
        if disk not in io_init:
            continue
        io_stat_prev = io_init[disk]
        # for io_curr, io_prev in zip(io_stat_curr, io_stat_prev):
        io_diff = ( curr - prev for curr, prev in zip(io_stat_curr, io_stat_prev) )
        read_count, write_count, read_bytes, write_bytes, read_time, write_time, read_merged_count, write_merged_count, busy_time = io_diff
        push(stats, f'io {disk} read Kbytes', read_bytes / 10**3)
        push(stats, f'io {disk} write Kbytes', write_bytes / 10**3)
        push(stats, f'io {disk} busy_time', busy_time)
    io_init = io

    # 
    cpu_stats = psutil.cpu_stats()
    ctx_switches, interrupts, soft_interrupts, syscalls = ( curr - prev for curr, prev in zip(cpu_stats, cpu_stats_init) )
    cpu_stats_init = cpu_stats
    push(stats, f'ctx switches kilo', ctx_switches / 10**3)
    # 
# 
print(stats)
for key, values in stats.items():
    # plt.figure(1)
    # plt.subplot(211)
    # plt.plot(t1, f(t1), 'bo', t2, f(t2), 'k')
    print(key, '\t', type(values), '\t', len(values), '\t', values[0])
    if max(values) < 1:
        continue
    cealing = max(values, 1)
    # values = [ v / cealing for v in values ]
    plt.plot(values)
plt.ylabel('some numbers')
plt.show()
