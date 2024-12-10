from framing.frameplayer import FramePlayer
from framing.framers.streamframer import StreamFramer
from ledmat import LEDMatrix
from ledmat.ledsim import sim_frame
import argparse

BRIGHTNESS = 0.50
SIMULATE = True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="Door Net Receiver")
    parser.add_argument("url")
    parser.add_argument("password")
    parser.add_argument("-b", "--brightness", default=0.5)
    parser.add_argument("-s", "--sim", default=False)
    args = parser.parse_args()

    # Create the framer
    framer = StreamFramer(args.url, args.password)

    if args.sim:
        sim_frame(framer)
    else:
        # Create the frame player
        led_matrix = LEDMatrix(brightness=args.brightness, gamma=2.2, contrast=1.0)
        player = FramePlayer(led_matrix, framer)

        # Play the frames
        player.play()
