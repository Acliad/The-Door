#include <OctoWS2811.h>

#define SOF_FLAG '*' // Start of frame flag

const int leds_per_column = 124;
const int num_columns = 50;
const int columns_per_bank = 4;
// Blank pixels around the door handle. 
const int num_blank_pixels = 28;
// The second to last bank of LEDs is missing 16 pixels due to the handle, so we need to add dummy pixels back in to
// make the matrix work
const int num_dummy_pixels = 16; 
const int ledsPerStrip = leds_per_column * columns_per_bank; 
// There are 50 column on the door, each bank contains 4 columns. The last bank contains 3 columns but it must have 4 in
// software.
const int numBanks = 13; 
const int dummy_start_index = columns_per_bank*leds_per_column*3*(numBanks-1) - num_dummy_pixels*3;
const int dummy_end_index = dummy_start_index + num_dummy_pixels*3;

// The physical number of LEDs on the door.
const int real_num_leds = leds_per_column * num_columns - num_blank_pixels; 
const uint8_t pinList[numBanks] = {12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0};

// The display buffers need to have 24 bits per pixel but are stored in 32 bit integers.
const int bufferSize = ledsPerStrip*3*numBanks*(24/32 + 0.5);
DMAMEM int displayMemory[bufferSize];
int drawingMemory[bufferSize];

const int config = WS2811_GRB | WS2811_800kHz;

OctoWS2811 leds(ledsPerStrip, displayMemory, drawingMemory, config, numBanks, pinList);

void setup() {
  Serial.begin(115200);
  // TODO: Adjust the timeout to be on the order of ~2 frames. 
  Serial.setTimeout(30);
  leds.begin();
  leds.show();
}

void loop() {
  // Wait for SOF_FLAG
  int start_char = Serial.read();
  if (start_char == SOF_FLAG) {
    // Serial.println("SOF Received"); 
    // A frame has started, so we expect to receive 3*numLEDs bytes total, but we need
    // to insert our dummy pixels.
    int num_bytes = Serial.readBytes((char *)drawingMemory, dummy_start_index);
    // If readBytes timed out, restart the loop.
    if (num_bytes < 0) {
      return;
    }
    num_bytes += Serial.readBytes((char *)drawingMemory+dummy_end_index, real_num_leds*3-dummy_start_index);
    // Serial.print("Num bytes received: ");
    // Serial.println(num_bytes);
    // Check if we received the correct number of bytes. If not, wait for another SOF and try again.
    if (num_bytes == real_num_leds*3) {
      // We received the correct number of bytes, so we can show the frame.
      leds.show();
    } 
  }
}