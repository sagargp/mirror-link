import argparse
import numpy as np
import matplotlib.pyplot as plt
import grpc
import queue
from concurrent import futures
from google.protobuf import struct_pb2

import mirror_pb2
import mirror_pb2_grpc


class AudioService(mirror_pb2_grpc.AudioServiceServicer):
    def __init__(self, q):
        self._queue = q

    def sendAudio(self, request, context):
        self._queue.put(request.data)
        return struct_pb2.Value()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('ip', default='127.0.0.1')
    parser.add_argument('port', default='9999')
    args = parser.parse_args()

    # main(chunk_size=2048, ip=args.ip, port=args.port)

    q = queue.Queue()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    mirror_pb2_grpc.add_AudioServiceServicer_to_server(AudioService(q), server)
    server.add_insecure_port('0.0.0.0:9999')
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
            data = q.get()
            data = np.frombuffer(data, np.int16)

            # Force the new data into the plot, but without redrawing axes.
            audio_plot.set_xdata(np.arange(len(data)))
            audio_plot.set_ydata(data)

            # Show the updated plot, but without blocking
            plt.pause(0.001)
            q.task_done()
        except KeyboardInterrupt:
            running = False
        except queue.Empty:
            pass

    q.join()
    server.stop(0)
