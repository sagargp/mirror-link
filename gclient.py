import pyaudio
import argparse
import grpc
import mirror_pb2
import mirror_pb2_grpc


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('server', default='127.0.0.1')
    parser.add_argument('port', default='9999')
    parser.add_argument('chunk_size', type=int, default=2048)
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

    print("\n+---------------------------------+")
    print("| Press Ctrl+C to Break Recording |")
    print("+---------------------------------+\n")

    # Loop so program doesn't end while the stream is open
    running = True
    while running:
        try:
            audio_data = stream.read(args.chunk_size, exception_on_overflow=False)
            stub.sendAudio(mirror_pb2.AudioChunk(data=audio_data))
        except KeyboardInterrupt:
            running = False

    # Close up shop
    stream.stop_stream()
    stream.close()
    audio.terminate()


