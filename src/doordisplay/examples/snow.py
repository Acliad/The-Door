from frames.framers.animsnowflake import AnimSnowflake
from frames.frameplayer import FramePlayer

BRIGHTNESS = 0.40

snow = AnimSnowflake()

player = FramePlayer(snow, brightness=BRIGHTNESS, gamma=2.2, contrast=1.0)

player.play()
