import sys
import numpy as np
import time
import argparse
from threading import Lock
import queue
import grpc
from concurrent import futures

import mirror_pb2
import mirror_pb2_grpc


FRAMESPERBUFFER = 2048
LOOPTIMEMS = 0.046


class AudioService(mirror_pb2_grpc.AudioServiceServicer):
    def __init__(self):
        self._input_lock = Lock()
        self._output_lock = Lock()
        self._incoming_messages = {}
        self._outgoing_messages = queue.Queue()
        self._last_time = time.perf_counter()

    def _enqueue_chunk(self, chunk):
        with self._input_lock:
            self._incoming_messages[chunk.sender] = chunk

            if time.perf_counter() - self._last_time > LOOPTIMEMS:
                summed_float = np.empty([FRAMESPERBUFFER, 1], dtype=np.int16)

                for sender, chunk in self._incoming_messages.items():
                    chunk_int = np.frombuffer(chunk.data, dtype=np.int16)
                    for i in range(FRAMESPERBUFFER):
                        summed_float[i] = summed_float[i] + np.float64(chunk_int[i])
                self._incoming_messages = {}

                summed = np.clip(summed_float, np.iinfo(np.int16).min, np.iinfo(np.int16).max).tobytes()

                with self._output_lock:
                    outgoing = mirror_pb2.AudioChunk(
                        sender=chunk.name,
                        data=summed,
                        id=chunk.id)
                    self._outgoing_messages.put(outgoing)
                self._last_time = time.perf_counter()

    def SendAudio(self, request, context):
        self._enqueue_chunk(request)
        return mirror_pb2.Empty()

    def SendAudioStream(self, request_iterator, context):
        for chunk in request_iterator:
            self._enqueue_chunk(chunk)
        return mirror_pb2.Empty()

    def GetAudioStream(self, request_iterator, context):
        while not self._outgoing_messages.empty():
            yield self._outgoing_messages.get()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('ip', default='127.0.0.1')
    parser.add_argument('port', default='9999')
    args = parser.parse_args()

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    service = AudioService()
    mirror_pb2_grpc.add_AudioServiceServicer_to_server(service, server)
    server.add_insecure_port(f'{args.ip}:{args.port}')
    server.start()

    running = True
    while running:
        try:
            time.sleep(0.1)
        except KeyboardInterrupt:
            running = False
    server.stop(0)
