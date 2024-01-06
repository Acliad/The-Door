This project is a door mounted LED matrix that can be driven from any computer with a USB port. Firmware running on a Teensy 4 manages the LED matrix on the door and recieves byte streams over USB to control the LEDs. A python script running on the host computer sends the byte streams to the Teensy. 

For more information on the Python side, including an example of how to create new animations, see the [doordisplay readme](src/doordisplay/readme.md).

## TODO:
- [ ] Create a GUI for easily controlling the matrix
- [ ] Add a readme to the `src/teensy` folder
- [ ] Add more project details to the main readme
- [ ] Add a visual filter to the LEDSimulator to make the pixels look glowy like the real thing
- [x] Update framers and FramePlayer method to use a return dict of {frame, duration}
- [x] Add the ability to resize the LEDSimulator window