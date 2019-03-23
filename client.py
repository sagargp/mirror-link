import pyaudio
import numpy as np
import socket
import struct
import argparse


def send(ip, port, data):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(data, (ip, int(port)))


def main(chunk_size, server, port):
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
    print( "+---------------------------------+\n")

    # audio_plot, dfft_plot = setup_plots()

    # Loop so program doesn't end while the stream is open
    running = True
    while running:
        try:
            audio_data = stream.read(chunk_size, exception_on_overflow=False)

            # get and convert the data to float
            audio_data = np.fromstring(audio_data, np.int16)

            print(max(audio_data))

            send(server, port, audio_data)

            # Fast Fourier Transform, 10*log10(abs) is to scale it to dB
            # and make sure it's not imaginary
            dfft = 10.*np.log10(abs(np.fft.rfft(audio_data)))

            # Force the new data into the plot, but without redrawing axes.
            # audio_plot.set_xdata(np.arange(len(audio_data)))
            # audio_plot.set_ydata(audio_data)
            # dfft_plot.set_xdata(np.arange(len(dfft))*10.)
            # dfft_plot.set_ydata(dfft)

            # # Show the updated plot, but without blocking
            # plt.pause(0.01)
        except KeyboardInterrupt:
            running = False

    # Close up shop
    stream.stop_stream()
    stream.close()
    audio.terminate()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('server', default='127.0.0.1')
    parser.add_argument('port', default='9999')
    args = parser.parse_args()

    main(chunk_size=1024, server=args.server, port=args.port)
