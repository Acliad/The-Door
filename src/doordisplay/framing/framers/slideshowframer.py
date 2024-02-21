from framing.framers.framer import Framer
from PIL import Image
import numpy as np
from pathlib import Path
from framing.utils import scale_fit, clip, shift
from typing import List
import random
from enum import Enum
import time

class TransitionType(Enum):
    NONE = 1
    SIMPLE_LR = 2
    SIMPLE_RL = 3
    SIMPLE_UD = 4
    SIMPLE_DU = 5
    SIMPLE_FADE = 6
    RANDOM = 7

class SlideshowFramer(Framer):
    def __init__(self, image_paths: List[str | Path],
                 transition_type: TransitionType, 
                 auto_scale: bool = True,
                 display_duration: float = 2.0,
                 shuffle: bool = True,
                 transition_duration: float = 1.0):
        super().__init__()
        self.auto_scale = auto_scale
        self.image_paths = image_paths
        self.shuffle = shuffle
        self.matrix = np.zeros((self.HEIGHT, self.WIDTH, 3), dtype=np.uint8)
        self.display_duration = display_duration
        self.global_transition_type = transition_type
        self.transition_type = transition_type
        self.transition_duration = transition_duration
        self.transition_position = 0.0
        self.image_path_indicies = []
        self.update_indicies()
        self.next_image = self._load_next_image()
        
        if self.global_transition_type == TransitionType.RANDOM:
            self.transition_type = self._choose_random_transition()
        
    def update_indicies(self):
        if self.shuffle:
            self.image_path_indicies = random.sample(range(0, len(self.image_paths)), len(self.image_paths))
        else:
            self.image_path_indicies = list(range(len(self.image_paths)))

    def update(self):
        
        if(self.transition_type == TransitionType.NONE):
            self._update_image_no_transition()

        elif(self.transition_type == TransitionType.SIMPLE_LR):
            self._update_image_left_right() 

        elif(self.transition_type == TransitionType.SIMPLE_RL):
            self._update_image_right_left()

        elif(self.transition_type == TransitionType.SIMPLE_UD):
            self._update_image_up_down()

        elif(self.transition_type == TransitionType.SIMPLE_DU):
            self._update_image_down_up()

        elif(self.transition_type == TransitionType.SIMPLE_FADE):
            self._update_image_fade()
              
        return super().update()
    
    def reset(self):
        self.matrix = np.zeros((self.HEIGHT, self.WIDTH, 3), dtype=np.uint8)
        self.update_indicies()
        self.transition_position = 0.0
        self.next_image = self._load_next_image()

    def _load_next_image(self) -> np.ndarray:
        # Open the next image
        image_path = self.image_paths[self.image_path_indicies.pop(0)]
        image = Image.open(image_path)
        
        if self.auto_scale:
            image = scale_fit(image, self.WIDTH, self.HEIGHT)
        else:
            image = clip(image, self.WIDTH, self.HEIGHT)

        #Reset the shuffled list once it's empty
        if not self.image_path_indicies:
            self.update_indicies()

        return np.array(image)
    
    def _choose_random_transition(self) -> TransitionType:
        return random.choice([e for e in TransitionType if e != TransitionType.NONE 
                                                    and e != TransitionType.RANDOM])    

    def _end_transition(self):
        #reset the index and end update the duration
        self.dt = self.display_duration
        self.transition_position = 0.0
        self.next_image = self._load_next_image()

        if self.global_transition_type == TransitionType.RANDOM:
            self.transition_type = self._choose_random_transition()

    def _increment_position(self):
        #calcualte new transition position
        self.transition_position += self.dt / self.transition_duration
        self.transition_position = min(self.transition_position, 1)
        
            
    def _update_image_no_transition(self):
        #load the new image
        self.dt = self.display_duration
        self.matrix = self._load_next_image()

    def _update_image_left_right(self):
        #start the transition
        if self.transition_position == 0.0:
            self.dt = 1 / Framer.DEFAULT_FRAMERATE
        
        shift_index = round(self.transition_position * self.WIDTH)
        
        # Copy columns from the new image to the existing image
        self.matrix[:, :shift_index] = self.next_image[:, :shift_index]
    
        #calcualte new transition position
        self._increment_position()

        #End the transition
        if shift_index == self.WIDTH:
            self._end_transition()

    def _update_image_right_left(self):
        # Start the transition
        if self.transition_position == 0.0:
            self.dt = 1 / Framer.DEFAULT_FRAMERATE

        shift_index = round(self.transition_position * self.WIDTH)
         
        # Copy columns from the new image to the existing image
        self.matrix[:, self.WIDTH - shift_index:] = self.next_image[:, :shift_index]

        #calcualte new transition position
        self._increment_position()

        # End the transition
        if shift_index == self.WIDTH:      
            self._end_transition()

    def _update_image_up_down(self):
        # Start the transition
        if self.transition_position == 0.0:
            self.dt = 1 / Framer.DEFAULT_FRAMERATE

        shift_index = round(self.transition_position * self.HEIGHT)
                 
        # Copy columns from the new image to the existing image
        self.matrix[self.HEIGHT - shift_index:, :] = self.next_image[:shift_index, :]

        #calcualte new transition position
        self._increment_position()

        # End the transition
        if shift_index == self.HEIGHT:
            self._end_transition()

    def _update_image_down_up(self):
        # Start the transition
        if self.transition_position == 0:
            self.dt = 1 / Framer.DEFAULT_FRAMERATE

        shift_index = round(self.transition_position * self.HEIGHT)

        # Copy columns from the new image to the existing image
        self.matrix[:shift_index :] = self.next_image[:shift_index, :]

        #calcualte new transition position
        self._increment_position()

        # End the transition
        if shift_index == self.HEIGHT: 
            self._end_transition()

    def _update_image_fade(self):
        if self.transition_position == 0:
            self.dt = 1 / Framer.DEFAULT_FRAMERATE

        # Calculate blend factor based on shift index
        blend_factor = self.transition_position
        
        # Blend the two images together
        self.matrix = (1 - blend_factor) * self.matrix + blend_factor * self.next_image

        #calcualte new transition position
        self._increment_position()

        # End the transition
        if blend_factor == 1.0:
            self._end_transition()
