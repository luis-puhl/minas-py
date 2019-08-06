import logging
import time

import psutil
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

log = logging.getLogger(__name__)
log.info(__name__)

class MonitorBase():
    def __init__(self):
        self.columns = []
        try:
            self.capable = True
            stats = self.gather()
            for column, value in stats.items():
                self.columns.append(column)
        except Exception as ex :
            print('not capable', ex)
            self.capable = False

class MonitorSensorsTemperatures(MonitorBase):
    # 'sensors_temperatures'
    def gather(self):
        if not self.capable:
            return []
        stats = {}
        for device, cores in psutil.sensors_temperatures().items():
            for shwtemp in cores:
                label, current, high, critical = shwtemp
                stats[f'temp_{device}_{label}'] = current
        return stats
class MonitorCpuStats(MonitorBase):
    # 'cpu_stats'
    def gather(self):
        if not self.capable:
            return []
        stats = {}
        if not hasattr(self, 'cpu_stats_init'):
            self.cpu_stats_init = psutil.cpu_stats()
        # 
        cpu_stats = psutil.cpu_stats()
        ctx_switches, interrupts, soft_interrupts, syscalls = ( curr - prev for curr, prev in zip(cpu_stats, self.cpu_stats_init) )
        self.cpu_stats_init = cpu_stats
        stats[f'kilo_ctx_switches'] = ctx_switches / 10**3
        return stats
class MonitorDiskIoCounters(MonitorBase):
    # 'disk_io_counters'
    def gather(self):
        if not self.capable:
            return []
        stats = {}
        if not hasattr(self, 'io_init'):
            self.io_init = psutil.disk_io_counters(perdisk=True)
        # 
        io = psutil.disk_io_counters(perdisk=True)
        for disk, io_stat_curr in io.items():
            if disk not in self.io_init:
                continue
            io_stat_prev = self.io_init[disk]
            # for io_curr, io_prev in zip(io_stat_curr, io_stat_prev):
            io_diff = ( curr - prev for curr, prev in zip(io_stat_curr, io_stat_prev) )
            if len(io_stat_curr) == 6:
                read_count, write_count, read_bytes, write_bytes, read_time, write_time = io_diff
                read_merged_count, write_merged_count, busy_time = 0, 0, 0
            if len(io_stat_curr) == 9:
                read_count, write_count, read_bytes, write_bytes, read_time, write_time, read_merged_count, write_merged_count, busy_time = io_diff
            stats[f'io_{disk}_read_Mbytes'] = read_bytes / 10**6
            stats[f'io_{disk}_write_Mbytes'] = write_bytes / 10**6
            stats[f'io_{disk}_busy_time'] = busy_time
        self.io_init = io
        # 
        return stats
class MonitorVirtualMemory(MonitorBase):
    # 'virtual_memory'
    def gather(self):
        if not self.capable:
            return []
        stats = {}
        # 
        virtual_memory = psutil.virtual_memory()
        if len(virtual_memory) == 5:
            total, available, percent, used, free = virtual_memory
            active, inactive, buffers, cached, shared, slab = 0, 0, 0, 0, 0, 0
        if len(virtual_memory) == 11:
            total, available, percent, used, free, active, inactive, buffers, cached, shared, slab = virtual_memory
        stats[f'ram_percent'] = percent
        stats[f'ram_GB'] = used / 10**9 
        # 
        return stats
class MonitorCpuFreq(MonitorBase):
    # 'cpu_freq'
    def gather(self):
        if not self.capable:
            return []
        stats = {}
        # 
        current, _min, _max = psutil.cpu_freq()
        stats[f'cpu_freq_GHz'] = current / 10**3
        # 
        return stats
class MonitorCpuPercent(MonitorBase):
    # 'cpu_percent'
    def gather(self):
        if not self.capable:
            return []
        stats = {}
        # 
        cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
        for i, core_uesed in enumerate(cpu_percent):
            stats[f'cpu_percent_{i}'] = core_uesed
        # 
        return stats

class ResourcesMonitor():
    def __init__(self):
        self.columns = ['time']
        self.gather_functions = []
        # 
        monitors = [
            MonitorSensorsTemperatures(),
            MonitorCpuStats(),
            MonitorDiskIoCounters(),
            MonitorVirtualMemory(),
            MonitorCpuFreq(),
            MonitorCpuPercent(),
        ]
        for monitor in monitors:
            if monitor.capable:
                self.columns.extend(monitor.columns)
                self.gather_functions.append(monitor.gather)
        # 
        self.stats = []
        # 
    def gather_all_stats(self):
        values = { 'time': pd.datetime.fromtimestamp(int(time.time())) }
        for gather in self.gather_functions:
            for key, value in gather().items():
                values[key] = value
        self.stats.append(values)
        return self.stats


if __name__ == '__main__':
    resourcesMonitor = ResourcesMonitor()
    try:
        while True:
            resourcesMonitor.gather_all_stats()
    except KeyboardInterrupt:
        pass
    # 
    df = pd.DataFrame(data=resourcesMonitor.stats)
    df.to_csv('sys_monitor.py.csv')
    print(df)
    # 
    plt.close('all')
    fig, ax = plt.subplots(figsize=(19.20,10.80))
    # ax.set_yscale('log')
    # 
    # df= pd.read_csv('sys_monitor.py.csv')
    df.index = df['time']
    df = df.drop(columns=['Unnamed: 0', 'time'])
    # aggregate cpu
    cpu_perc = [col for col in df.columns if 'cpu_perc' in col]
    df['cpu_perc'] = df[cpu_perc].sum(axis=1)
    df['busy_cores'] = (cpu_df > 50).sum(axis=1) / len(cpu_perc)
    df = df.drop(cpu_perc, axis=1)
    # Skip low changes
    # avg = df.std().sum() / len(df.std())
    whoDrops = df.std()[df.std() < 1].index.values
    whoDrops = [ cl for cl in whoDrops if cl not in ['cpu_perc', 'busy_cores'] ]
    df_normal = df.drop(whoDrops, axis=1)
    # Normalize
    df_normal = df_normal /df_normal.max()
    # plot
    df_normal.plot(ax=ax)
    # view and save
    fig.tight_layout()
    fig.savefig('sys_monitor.png', dpi=100)
    plt.show()
