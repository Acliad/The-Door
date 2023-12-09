from frames.framers.animrainbow import AnimRainbow
from frames.frameplayer import FramePlayer
from time import sleep
import signal

BRIGHTNESS = 0.40

rainbow = AnimRainbow()
rainbow.speed = 1
rainbow.frequency = 1
player = FramePlayer(rainbow, brightness=BRIGHTNESS, gamma=2.2, contrast=1.0)


def handle_keyboard_interrupt(signal, frame):
    player.stop()
    print("Keyboard interrupt")

# Register the signal handler
signal.signal(signal.SIGINT, handle_keyboard_interrupt)

player.play()


while True:
    choice = input("Brightness: B[value] | Speed: S[value] | Frequency: F[value] | Saturation: A[value] | Quit: Q\n")
    choice = choice.upper()
    match choice[0]:
        case "B":
            BRIGHTNESS = float(choice[1:])
            player.brightness = BRIGHTNESS
        case "S":
            rainbow.speed = float(choice[1:])
        case "F":
            rainbow.frequency = float(choice[1:])
        case "A":
            rainbow.saturation = float(choice[1:])
        case "Q":
            player.stop()
            exit()
        case _:
            print("Invalid input")
