import pyaudio
import numpy as np
import matplotlib.pyplot as plt


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


def main(chunk_size):
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

    audio_plot, dfft_plot = setup_plots()

    # Loop so program doesn't end while the stream is open
    running = True
    while running:
        try:
            audio_data = stream.read(chunk_size, exception_on_overflow=False)

            # get and convert the data to float
            audio_data = np.fromstring(audio_data, np.int16)

            print(max(audio_data))

            # Fast Fourier Transform, 10*log10(abs) is to scale it to dB
            # and make sure it's not imaginary
            dfft = 10.*np.log10(abs(np.fft.rfft(audio_data)))

            # Force the new data into the plot, but without redrawing axes.
            audio_plot.set_xdata(np.arange(len(audio_data)))
            audio_plot.set_ydata(audio_data)
            dfft_plot.set_xdata(np.arange(len(dfft))*10.)
            dfft_plot.set_ydata(dfft)

            # Show the updated plot, but without blocking
            plt.pause(0.01)
        except KeyboardInterrupt:
            running = False

    # Close up shop
    stream.stop_stream()
    stream.close()
    audio.terminate()


if __name__ == '__main__':
    main(1024)
