import logging

import psutil
import matplotlib.pyplot as plt

log = logging.getLogger(__name__)
log.info(__name__)

class ResourcesMonitor():
    def __init__(self):
        self.capabilities = {
            'cpu_stats': lambda: psutil.cpu_stats(),
            'disk_io_counters': lambda: psutil.disk_io_counters(perdisk=True),
            'sensors_temperatures': lambda: psutil.sensors_temperatures().items(),
            'virtual_memory': lambda: psutil.virtual_memory(),
            'cpu_freq': lambda: psutil.cpu_freq(),
            'cpu_percent': lambda: psutil.cpu_percent(interval=1, percpu=True),
        }
        self.capabilities_enabled = []
        for name, func in self.capabilities.items():
            if self.check_capability(name, func):
                self.capabilities_enabled.append(name)
        # 
        self.stats = {}
        self.cpu_stats_init = psutil.cpu_stats()
        self.io_init = psutil.disk_io_counters(perdisk=True)
    def check_capability(self, name, func):
        try:
            func()
        except:
            return False
        return True
    def push(self, key, value):
        if key not in self.stats:
            self.stats[key] = list()
        self.stats[key].append(value)
    def gather_all_stats(self):
        self.gather_temps()
        self.gather_ram()
        self.gather_cpu_freq()
        self.gather_cpu_percent()
        self.gather_disk_io_counters()
        self.gather_cpu_stats()
    def gather_temps(self):
        if 'sensors_temperatures' not in self.capabilities_enabled:
            return
        for device, cores in psutil.sensors_temperatures().items():
            for shwtemp in cores:
                label, current, high, critical = shwtemp
                self.push(f'temp {device} {label}', current)
    def gather_ram(self):
        if 'virtual_memory' not in self.capabilities_enabled:
            return
        virtual_memory = psutil.virtual_memory()
        if len(virtual_memory) == 5:
            total, available, percent, used, free = virtual_memory
            active, inactive, buffers, cached, shared, slab = 0, 0, 0, 0, 0, 0
        if len(virtual_memory) == 11:
            total, available, percent, used, free, active, inactive, buffers, cached, shared, slab = virtual_memory
        self.push(f'ram percent', percent)
        self.push(f'ram used GB', used / 10**9 )
    def gather_cpu_freq(self):
        if 'cpu_freq' not in self.capabilities_enabled:
            return
        current, _min, _max = psutil.cpu_freq()
        self.push(f'cpu freq GHz', current / 10**3)
    def gather_cpu_percent(self):
        if 'cpu_percent' not in self.capabilities_enabled:
            return
        cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
        for i, core_uesed in enumerate(cpu_percent):
            self.push(f'cpu percent {i}', core_uesed)
    def gather_disk_io_counters(self):
        if 'disk_io_counters' not in self.capabilities_enabled:
            return
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
            self.push(f'io {disk} read Mbytes', read_bytes / 10**6)
            self.push(f'io {disk} write Mbytes', write_bytes / 10**6)
            self.push(f'io {disk} busy_time', busy_time)
        self.io_init = io
    def gather_cpu_stats(self):
        if 'cpu_stats' not in self.capabilities_enabled:
            return
        cpu_stats = psutil.cpu_stats()
        ctx_switches, interrupts, soft_interrupts, syscalls = ( curr - prev for curr, prev in zip(cpu_stats, self.cpu_stats_init) )
        self.cpu_stats_init = cpu_stats
        self.push(f'ctx switches kilo', ctx_switches / 10**3)

if __name__ == '__main__':
    resourcesMonitor = ResourcesMonitor()
    for i in range(10):
        resourcesMonitor.gather_all_stats()
    # 
    print(resourcesMonitor.stats)
    for key, values in resourcesMonitor.stats.items():
        # print(key, '\t', type(values), '\t', len(values), '\t', values[0])
        cealing = max(values)
        if cealing < 1:
            continue
        plt.plot(values, label=key)
    plt.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc='lower left', ncol=4, mode='expand', borderaxespad=0.)
    plt.tight_layout()
    plt.show()
    plt.savefig('sys_monitor.png')
