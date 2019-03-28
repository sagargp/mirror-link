import time
import pyaudio
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
    def __init__(self):
        self._last_message = None

    def SendAudio(self, request, context):
        self._last_message = request
        return mirror_pb2.Empty()

    def GetAudioStream(self, request_iterator, context):
        last_sent_message_id = None
        while True:
            if self._last_message and self._last_message.id != last_sent_message_id:
                yield self._last_message
                last_sent_message_id = self._last_message.id


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('ip', default='127.0.0.1')
    parser.add_argument('port', default='9999')
    args = parser.parse_args()

    # main(chunk_size=2048, ip=args.ip, port=args.port)

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    service = AudioService()
    mirror_pb2_grpc.add_AudioServiceServicer_to_server(service, server)
    server.add_insecure_port('0.0.0.0:9999')
    server.start()

    # first setup the plots
    # f, ax = plt.subplots(2)

    # # Prepare the Plotting Environment with random starting values
    # x = np.arange(10000)
    # y = np.random.randn(10000)

    # # Plot 0 is for raw audio data
    # audio_plot, = ax[0].plot(x, y)
    # ax[0].set_xlim(0, 1024)
    # ax[0].set_ylim(-5000, 5000)
    # ax[0].set_title("Raw Audio Signal")

    # # Show the plot, but without blocking updates
    # plt.tight_layout()
    # plt.subplots_adjust(hspace=0.3)

    # create an audio object
    audio = pyaudio.PyAudio()

    # open stream based on the wave object which has been input.
    stream = audio.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=44100,
        output=True)

    running = True
    last_id = None
    while running:
        try:
            # if np.abs(np.average(np.frombuffer(data, np.int16))) > 30.0:
            # Force the new data into the plot, but without redrawing axes.
            # audio_plot.set_xdata(np.arange(len(data)))
            # audio_plot.set_ydata(data)
            # stream.write(data)
            if service._last_message and last_id != service._last_message.id:
                stream.write(service._last_message.data)
                last_id = service._last_message.id

                # Show the updated plot, but without blocking
                # plt.pause(1/44100.)
        except KeyboardInterrupt:
            running = False

    server.stop(0)
    stream.close()
    audio.terminate()
