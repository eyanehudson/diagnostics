#!/usr/bin/env python3

import collections
import socket
import psutil
from diagnostic_msgs.msg import DiagnosticStatus
from diagnostic_updater import DiagnosticTask, Updater
import rclpy
from rclpy.logging import get_logger

class NetworkTask(DiagnosticTask):

    def __init__(self, window):
        super().__init__('Network Information')
        self._readings = collections.deque(maxlen=window)

    def run(self, stat):
        net_info = psutil.net_io_counters(pernic=True, nowrap=True)

        for iface, data in net_info.items():
            stat.add(f'{iface} GBytes Sent', f'{data.bytes_sent / (1024 ** 3):.3f}')
            stat.add(f'{iface} GBytes Received', f'{data.bytes_recv / (1024 ** 3):.3f}')
            stat.add(f'{iface} Packets Sent', str(data.packets_sent))
            stat.add(f'{iface} Packets Received', str(data.packets_recv))
            stat.add(f'{iface} Packets Dropped (in)', str(data.dropin))
            stat.add(f'{iface} Packets Dropped (out)', str(data.dropout))

            # Check for dropped packets
            if data.dropin > 10 or data.dropout > 10: # user defined threshold for dropped packets #TODO: update this
                warning_msg = f"Packet drops detected on {iface}: In={data.dropin}, Out={data.dropout}"
                stat.summary(DiagnosticStatus.WARN, warning_msg)
                get_logger('network_monitor').warn(warning_msg)
            else:
                stat.summary(DiagnosticStatus.OK, f'No packet drops detected on')

        return stat

def main():
    hostname = socket.gethostname()
    cleaned_hostname = ''.join(c if (c.isascii() and c.isalnum()) else '_' for c in hostname)
    
    rclpy.init()
    node = rclpy.create_node(f'network_monitor_{cleaned_hostname}')
    updater = Updater(node)
    updater.setHardwareID(hostname)
    
    updater.add(NetworkTask(node.declare_parameter('window', 1).value))

    rclpy.spin(node)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
