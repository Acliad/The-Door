from frames.framers.animsnowflake import AnimSnowflake
from frames.frameplayer import FramePlayer
from ledmat import LEDMatrix
from ledmat.ledsim import sim_frame

SIMULATE = True

BRIGHTNESS = 0.8
TRAIL_FACTOR = 0
SPEED = 1.0


snow = AnimSnowflake(speed=SPEED, trail_factor=TRAIL_FACTOR)


if SIMULATE:
    # Simulated door
    sim_frame(snow)
else:
    # Real door
    led_matrix = LEDMatrix(brightness=BRIGHTNESS, gamma=2.2, contrast=1.0)
    player = FramePlayer(led_matrix, snow)
    try:
        player.play_blocking()
    except KeyboardInterrupt:
        player.stop()
        print("Exiting...")