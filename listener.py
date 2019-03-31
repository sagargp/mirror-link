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

    stream = audio.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=44100,
        output=True,
        frames_per_buffer=4410)

    # Open the connection and start streaming the data
    stream.start_stream()

    running = True
    while running:
        try:
            last_played = 0
            print('start')
            for chunk in stub.GetAudioStream(mirror_pb2.Empty()):
                if chunk.id != last_played:
                    print('read')
                    stream.write(chunk.data, 4410)
                    last_played = chunk.id
            print('stop')
        except KeyboardInterrupt:
            running = False

    # Close up shop
    stream.stop_stream()
    stream.close()
    audio.terminate()


