import time
import pyaudio
import argparse
import grpc
from concurrent import futures

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
            if service._last_message and last_id != service._last_message.id:
                stream.write(service._last_message.data)
                last_id = service._last_message.id

            time.sleep(1/2*44100.)
        except KeyboardInterrupt:
            running = False

    server.stop(0)
    stream.close()
    audio.terminate()
