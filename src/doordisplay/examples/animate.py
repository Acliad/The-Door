from frames.framers.animrainbow import AnimRainbow
from frames.frameplayer import FramePlayer
from ledmat import LEDMatrix
from ledmat.ledsim import sim_frame
from time import sleep
import signal

BRIGHTNESS = 0.40
SIMULATE = True

rainbow = AnimRainbow()
rainbow.speed = 1
rainbow.frequency = 1


if SIMULATE:
    sim_frame(rainbow)
else:
    led_matrix = LEDMatrix(brightness=BRIGHTNESS, gamma=2.2, contrast=1.0)
    player = FramePlayer(led_matrix, rainbow)
    player.play_blocking()

# def handle_keyboard_interrupt(signal, frame):
#     player.stop()
#     print("Keyboard interrupt")
#
# # Register the signal handler
# signal.signal(signal.SIGINT, handle_keyboard_interrupt)
#
# player.play()
#
# while True:
#     choice = input("Brightness: B[value] | Speed: S[value] | Frequency: F[value] | Saturation: A[value] | Quit: Q\n")
#     choice = choice.upper()
#     match choice[0]:
#         case "B":
#             BRIGHTNESS = float(choice[1:])
#             player.brightness = BRIGHTNESS
#         case "S":
#             rainbow.speed = float(choice[1:])
#         case "F":
#             rainbow.frequency = float(choice[1:])
#         case "A":
#             rainbow.saturation = float(choice[1:])
#         case "Q":
#             player.stop()
#             exit()
#         case _:
#             print("Invalid input")
