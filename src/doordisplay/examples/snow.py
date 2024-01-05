from frames.framers.animsnowflake import AnimSnowflake
from frames.frameplayer import FramePlayer
from ledmat import LEDMatrix
from ledmat.ledsim import sim_frame

SIMULATE = True

BRIGHTNESS = 0.8
TRAIL_FACTOR = 0
SPEED = 1.0
INTERPOLATE = False
STORM_FACTOR = 2

snow = AnimSnowflake(fall_speed=SPEED, 
                     storm_factor=STORM_FACTOR, 
                     interpolate=INTERPOLATE, 
                     trail_factor=TRAIL_FACTOR, 
                     wind_start_pos=10)

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