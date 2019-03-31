import numpy as np
import queue
import time
import threading
import uuid
import pyaudio
import argparse
import grpc
import mirror_pb2
import mirror_pb2_grpc


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('name')
    parser.add_argument('server', default='127.0.0.1')
    parser.add_argument('port', default='9999')
    args = parser.parse_args()

    channel = grpc.insecure_channel(f'{args.server}:{args.port}')
    stub = mirror_pb2_grpc.AudioServiceStub(channel)

    audio = pyaudio.PyAudio()

    # Claim the microphone
    stream = audio.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=44100,
        input=True,
        frames_per_buffer=2048)

    # Open the connection and start streaming the data
    stream.start_stream()

    def get_chunk():
        while True:
            data = stream.read(2048, exception_on_overflow=False)
            chunk = mirror_pb2.AudioChunk(
                sender=args.name,
                data=data,
                id=uuid.uuid4().hex)
            yield chunk

    while True:
        stub.SendAudioStream(get_chunk())

    # Close up shop
    stream.stop_stream()
    stream.close()
    audio.terminate()


