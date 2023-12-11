from frames.framers.animsnowflake import AnimSnowflake
from frames.frameplayer import FramePlayer
from ledmat import LEDMatrix

BRIGHTNESS = 0.40

snow = AnimSnowflake()

led_matrix = LEDMatrix(brightness=BRIGHTNESS, gamma=2.2, contrast=1.0)
player = FramePlayer(led_matrix, snow)

player.play()
