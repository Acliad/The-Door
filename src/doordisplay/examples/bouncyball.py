from framing.framers.animations.animbouncyball import AnimBouncyBall
from framing import FramePlayer
from ledmat.ledsim import sim_frame
from ledmat import LEDMatrix

SIMULATE = True
BRIGHTNESS = 0.6

bouncyball = AnimBouncyBall(num_balls=6, 
                            trail_factor=0.8, 
                            interpolate=False, 
                            collide=True)

if SIMULATE:
    sim_frame(bouncyball)
else:
    try:
        led_matrix = LEDMatrix(brightness=BRIGHTNESS)
        player = FramePlayer(led_matrix, bouncyball)
        player.play_blocking()
    except KeyboardInterrupt:
        print("Exiting...")