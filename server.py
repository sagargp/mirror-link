import struct
import time
import queue
from threading import Thread
import argparse
import numpy as np
import matplotlib.pyplot as plt
import socket


class UDPServer(Thread):

    def __init__(self, data_queue, ip, port, chunk_size, *args, **kwargs):
        self._queue = data_queue
        self._ip = ip
        self._port = port
        self._chunk_size = chunk_size
        self._running = True

        self.connected_clients = {}
        super().__init__(*args, **kwargs)

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((self._ip, int(self._port)))

        while self._running:
            data, addr = sock.recvfrom(self._chunk_size)
            name, data = struct.unpack('10s2038s', data)
            data = np.fromstring(data, np.int16)
            name = name.decode('ascii')
            self._queue.put(data)

            if name not in self.connected_clients:
                print('New client! {}'.format(name))
            self.connected_clients[name] = time.time()


def main(chunk_size, ip, port):
    # create a data queue
    q = queue.Queue()
    # start up the visualization thread
    server = UDPServer(q, ip, port, chunk_size)
    server.start()

    # first setup the plots
    f, ax = plt.subplots(2)

    # Prepare the Plotting Environment with random starting values
    x = np.arange(10000)
    y = np.random.randn(10000)

    # Plot 0 is for raw audio data
    audio_plot, = ax[0].plot(x, y)
    ax[0].set_xlim(0, 1024)
    ax[0].set_ylim(-5000, 5000)
    ax[0].set_title("Raw Audio Signal")

    # Show the plot, but without blocking updates
    plt.tight_layout()
    plt.subplots_adjust(hspace=0.3)

    running = True
    while running:
        try:
            data = q.get_nowait()
            # Force the new data into the plot, but without redrawing axes.
            audio_plot.set_xdata(np.arange(len(data)))
            audio_plot.set_ydata(data)

            # Show the updated plot, but without blocking
            plt.pause(0.001)
            q.task_done()
        except KeyboardInterrupt:
            running = False
            server._running = False
        except queue.Empty:
            pass

    q.join()
    server.join()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('ip', default='127.0.0.1')
    parser.add_argument('port', default='9999')
    args = parser.parse_args()

    main(chunk_size=2048, ip=args.ip, port=args.port)
