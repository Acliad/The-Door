from framing.framers.animations.animbouncyball import AnimBouncyBall
from ledmat.ledsim import sim_frame

bouncyball = AnimBouncyBall(num_balls=8)
sim_frame(bouncyball)