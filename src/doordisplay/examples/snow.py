from frames.framers.animsnowflake import AnimSnowflake
from frames.frameplayer import FramePlayer
from ledmat import LEDMatrix

BRIGHTNESS = 0.60

snow = AnimSnowflake()

led_matrix = LEDMatrix(brightness=BRIGHTNESS, gamma=2.2, contrast=1.0)
player = FramePlayer(led_matrix, snow)

try:
    player.play_blocking()
except KeyboardInterrupt:
    player.stop()
    print("Exiting...")
