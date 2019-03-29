import uuid
import pyaudio
import argparse
import grpc
import mirror_pb2
import mirror_pb2_grpc


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
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
        input=True)

    # Open the connection and start streaming the data
    stream.start_stream()

    running = True
    while running:
        try:
            audio_data = stream.read(2048, exception_on_overflow=False)
            stub.SendAudio(mirror_pb2.AudioChunk(sender='Sagar', data=audio_data, id=uuid.uuid4().hex))
        except KeyboardInterrupt:
            running = False

    # Close up shop
    stream.stop_stream()
    stream.close()
    audio.terminate()


