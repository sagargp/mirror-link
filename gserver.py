import sys
import numpy as np
import time
import pyaudio
import argparse
import grpc
from concurrent import futures

import mirror_pb2
import mirror_pb2_grpc


class AudioService(mirror_pb2_grpc.AudioServiceServicer):
    def __init__(self):
        self.messages = []
        self.last_message = None
        self.last_time = 0
        self.loop_time = 1/44100.

    def SendAudio(self, request, context):
        self.messages.append(
            np.frombuffer(request.data, np.int16))

        if time.perf_counter() - self.last_time > self.loop_time:
            request.data = sum(self.messages).tobytes()
            self.last_message = request
            self.last_time = time.perf_counter()
            # sys.stdout.write(f'{len(self.messages)}\n')
            self.messages = []
        return mirror_pb2.Empty()

    def GetAudioStream(self, request_iterator, context):
        last_sent_message_id = None
        while True:
            if self.last_message and self.last_message.id != last_sent_message_id:
                yield self.last_message
                last_sent_message_id = self.last_message.id


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
            if service.last_message and last_id != service.last_message.id:
                stream.write(service.last_message.data, 1024)
                last_id = service.last_message.id

            # time.sleep(1/32000.)
        except KeyboardInterrupt:
            running = False

    server.stop(0)
    stream.close()
    audio.terminate()
