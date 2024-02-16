from framing.framers.framer import Framer
import numpy as np
from framing.utils import place_in

class BouncyBall():

    def __init__(self,
                 x: float,
                 y: float,
                 speed_x: float,
                 speed_y: float,
                 size: int,
                 color: tuple[int, int, int] | list[int, int, int] | np.ndarray
                 ) -> None:
        self.x = x
        self.y = y
        self.speed_x = speed_x
        self.speed_y = speed_y
        self.size = size
        self.color = color
    
        self.matrix = np.zeros((self.size, self.size, 3), dtype=np.uint8)
        center = self.size//2
        radius = self.size/2

        # Create a meshgrid of x and y values
        x, y = np.meshgrid(np.arange(size), np.arange(size))

        # Use the circle equation to set values inside the circle to self.color
        circle_mask = (x - center)**2 + (y - center)**2 <= radius**2
        self.matrix[circle_mask, :] = self.color


class AnimBouncyBall(Framer):
    def __init__(self, num_balls: int = 8, 
                 trail_factor: float = 0.75, 
                 interpolate: bool = True,
                 collide: bool = True
                 ):
        super().__init__()
        
        # Create the matrix for the frame
        self.matrix = np.zeros((self.HEIGHT, self.WIDTH, 3), dtype=np.uint8)
        self.trail_factor = trail_factor
        self.interpolate = interpolate
        self.collide = collide

        self.balls: list[BouncyBall] = []
        for _ in range(num_balls):
            self.balls.append(BouncyBall(
                x=np.random.randint(0, self.WIDTH),
                y=np.random.randint(0, self.HEIGHT),
                speed_x=np.random.randint(20, 80),
                speed_y=np.random.randint(20, 80),
                size=2*np.random.randint(2, 7) + 1, # Odd numbers only
                color=np.random.randint(0, 255, 3)
            ))

    def update(self):
        # Apply the trail factor to the frame
        self.matrix = (self.matrix * self.trail_factor).astype(np.uint8)


        for i, ball in enumerate(self.balls):
            # Move the ball
            ball.x += ball.speed_x * self.dt
            ball.y += ball.speed_y * self.dt

            # Limit the ball's position to the frame
            ball.x = max(min(ball.x, self.WIDTH - ball.size), 0)
            ball.y = max(min(ball.y, self.HEIGHT - ball.size), 0)
            
            # If the ball hits the edge of the frame, reverse its direction
            if ball.x >= self.WIDTH - ball.size or ball.x <= 0:
                ball.speed_x *= -1
            if ball.y >= self.HEIGHT - ball.size or ball.y <= 0:
                ball.speed_y *= -1
            
            # check if balls should collide or not
            if self.collide:
                    # Check for collisions with other balls
                for j, other_ball in enumerate(self.balls):
                    if i != j and self.check_collision(ball, other_ball):
                        self.handle_collision(ball, other_ball)

            ball_x = ball.x if self.interpolate else round(ball.x)
            ball_y = ball.y if self.interpolate else round(ball.y)

            # Place the ball in the frame
            place_in(self.matrix, ball.matrix, ball_y, ball_x, transparent_threshold=10)
        return super().update()
    
    def check_collision(self, ball1, ball2):
        distance = np.sqrt((ball1.x - ball2.x)**2 + (ball1.y - ball2.y)**2)
        return distance <= (ball1.size + ball2.size) / 2

    def handle_collision(self, ball1, ball2):
        # Swap speeds to simulate bouncing off each other
        ball1.speed_x, ball2.speed_x = ball2.speed_x, ball1.speed_x
        ball1.speed_y, ball2.speed_y = ball2.speed_y, ball1.speed_y

    def reset(self):
        pass