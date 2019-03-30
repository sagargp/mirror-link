import threading
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


    def listener():
        audio = pyaudio.PyAudio()
        stream = audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=44100,
            output=True,
            frames_per_buffer=1024)

        while True:
            for chunk in stub.GetAudioStream(mirror_pb2.Empty()):
                stream.write(chunk.data, 1024)

    threading.Thread(target=listener).run()

    audio = pyaudio.PyAudio()

    # Claim the microphone
    stream = audio.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=44100,
        input_device_index=2,
        input=True,
        frames_per_buffer=1024)

    # Open the connection and start streaming the data
    stream.start_stream()

    running = True
    while running:
        try:
            audio_data = stream.read(1024, exception_on_overflow=False)
            stub.SendAudio(mirror_pb2.AudioChunk(sender='Sagar', data=audio_data, id=uuid.uuid4().hex))
        except KeyboardInterrupt:
            running = False

    # Close up shop
    stream.stop_stream()
    stream.close()
    audio.terminate()


