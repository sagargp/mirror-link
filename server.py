import argparse
import numpy as np
import matplotlib.pyplot as plt
import socket


def setup_plots():
    f, ax = plt.subplots(2)

    # Prepare the Plotting Environment with random starting values
    x = np.arange(10000)
    y = np.random.randn(10000)

    # Plot 0 is for raw audio data
    audio_plot, = ax[0].plot(x, y)
    ax[0].set_xlim(0, 1000)
    ax[0].set_ylim(-5000, 5000)
    ax[0].set_title("Raw Audio Signal")
    # Plot 1 is for the FFT of the audio
    dfft_plot, = ax[1].plot(x, y)
    ax[1].set_xlim(0, 5000)
    ax[1].set_ylim(0, 80)
    ax[1].set_title("Fast Fourier Transform")

    # Show the plot, but without blocking updates
    plt.tight_layout()
    plt.subplots_adjust(hspace=0.3)
    plt.pause(0.01)

    return audio_plot, dfft_plot


def main(chunk_size, ip, port):

    audio_plot, dfft_plot = setup_plots()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((ip, int(port)))

    # Loop so program doesn't end while the stream is open
    running = True
    while running:
        try:
            data, addr = sock.recvfrom(chunk_size)
            data = np.fromstring(data, np.int16)

            print(len(data))

            # Force the new data into the plot, but without redrawing axes.
            audio_plot.set_xdata(np.arange(len(data)))
            audio_plot.set_ydata(data)

            # Show the updated plot, but without blocking
            plt.pause(0.001)
        except KeyboardInterrupt:
            running = False


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('ip', default='127.0.0.1')
    parser.add_argument('port', default='9999')
    args = parser.parse_args()

    main(chunk_size=1024, ip=args.ip, port=args.port)
