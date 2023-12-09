#include <Arduino.h>
#line 1 "/Users/isaacrex/Library/Mobile Documents/com~apple~CloudDocs/Projects/The Door/src/the_door_test_teensy32/the_door_test_teensy32.ino"
#include <OctoWS2811.h>

#define SOF_FLAG '*' // Start of frame flag

const int leds_per_column = 10;
const int num_columns = 4;
const int numBanks = 4; 
const int real_num_leds = leds_per_column * num_columns; // The physical number of LEDs on the door.

DMAMEM int displayMemory[leds_per_column*8];
int drawingMemory[leds_per_column*8];

const int config = WS2811_GRB | WS2811_800kHz;

OctoWS2811 leds(leds_per_column, displayMemory, drawingMemory, config);

#line 17 "/Users/isaacrex/Library/Mobile Documents/com~apple~CloudDocs/Projects/The Door/src/the_door_test_teensy32/the_door_test_teensy32.ino"
void setup();
#line 32 "/Users/isaacrex/Library/Mobile Documents/com~apple~CloudDocs/Projects/The Door/src/the_door_test_teensy32/the_door_test_teensy32.ino"
void loop();
#line 17 "/Users/isaacrex/Library/Mobile Documents/com~apple~CloudDocs/Projects/The Door/src/the_door_test_teensy32/the_door_test_teensy32.ino"
void setup() {
  Serial.begin(115200);
  // TODO: Adjust the timeout to be on the order of ~2 frames. 
  Serial.setTimeout(100);
  Serial.println("Starting");
  leds.begin();
  // Set all LEDs to dim white
  for (int i=0; i < real_num_leds; i++) {
    // leds.setPixel(i, 0);
    leds.setPixel(i, 0x040404);
  }
  Serial.println("Setting all LEDs to dim white");
  leds.show();
}

void loop() {
  // Wait for SOF_FLAG
  int start_char = Serial.read();
  if (start_char == SOF_FLAG) {
    Serial.println("SOF Received");
    // A frame has started, so we expect to receive 3*numLEDs bytes.
    int num_bytes = Serial.readBytes((char *)drawingMemory, 3*real_num_leds);
    Serial.print("Num bytes received: ");
    Serial.println(num_bytes);
    uint8_t* drawingMemory8ptr = (uint8_t *)drawingMemory;
    for (int i=0; i < real_num_leds*3; i++) {
      int red = drawingMemory8ptr[i];
      int green = drawingMemory8ptr[i];
      int blue = drawingMemory8ptr[i];
      leds.setPixel(i, red, green, blue);
    }
    // Check if we received the correct number of bytes. If not, wait for another SOF and try again.
    if (num_bytes == real_num_leds*3) {
      // We received the correct number of bytes, so we can show the frame.
      leds.show();
    } 
  }
}

/*
#include <OctoWS2811.h>

#define MAX_TOTAL_MILLIAMPS 20000
#define MILLIAMPS_PER_COLOR 20

const int ledsPerStrip = 10;
const int numBanks = 4; 

// The display buffers need to have 24 bits per pixel but are stored in 32 bit integers.
const int bufferSize = ledsPerStrip*3*numBanks*(24/32 + 0.5);
DMAMEM int displayMemory[bufferSize];
int drawingMemory[bufferSize];

const int config = WS2811_GRB | WS2811_800kHz;

OctoWS2811 leds(ledsPerStrip, displayMemory, drawingMemory, config);

void setup() {
  leds.begin();
  Serial.begin(115200);
  leds.show();
}

// #define RED    0xFF0000
// #define GREEN  0x00FF00
// #define BLUE   0x0000FF
// #define YELLOW 0xFFFF00
// #define PINK   0xFF1088
// #define ORANGE 0xFF5000
// #define WHITE  0xFFFFFF

// Less intense...
#define RED    0x160000
#define GREEN  0x001600
#define BLUE   0x000016
#define YELLOW 0x101400
#define PINK   0x120009
#define ORANGE 0x100400
#define WHITE  0x101010

void loop() {
  int microsec = 2000000 / leds.numPixels();  // change them all in 2 seconds

  // uncomment for voltage controlled speed
  // millisec = analogRead(A9) / 40;

  colorWipe(RED, microsec);
  colorWipe(GREEN, microsec);
  colorWipe(BLUE, microsec);
  colorWipe(YELLOW, microsec);
  colorWipe(PINK, microsec);
  colorWipe(ORANGE, microsec);
  colorWipe(WHITE, microsec);
}

void colorWipe(int color, int wait)
{
  for (int i=0; i < leds.numPixels(); i++) {
    leds.setPixel(i, color);
    delayMicroseconds(wait);
    checkTotalBrightness();
    leds.show();
  }
    // // Test if we can directly manipulate the drawing buffer. Loop over every three bytes, setting then to the given 
    // // collor. Then call show() to copy the drawing buffer to the display buffer.
    // uint8_t green = (color >> 16) & 0xFF;
    // uint8_t red = (color >> 8) & 0xFF;
    // uint8_t blue = color & 0xFF;

    // uint8_t* displayMemory8ptr = (uint8_t *)drawingMemory;
    // for (int i=0; i < leds.numPixels(); i++) {
    //     displayMemory8ptr[i*3] = red;
    //     displayMemory8ptr[i*3+1] = green;
    //     displayMemory8ptr[i*3+2] = blue;
    // }
    // leds.show();
    // delayMicroseconds(wait*leds.numPixels());
}

// Checks the entire display buffer to see if the sum of values is set too high.
void checkTotalBrightness(){
    // Loop through each value in the drawing buffer, adding up the total brightness.
    uint8_t* displayMemoryPtrU8 = (uint8_t *)drawingMemory;
    uint32_t totalBrightness = 0;
    for (int i=0; i < leds.numPixels(); i++) {
        totalBrightness += displayMemoryPtrU8[i*3];
        totalBrightness += displayMemoryPtrU8[i*3+1];
        totalBrightness += displayMemoryPtrU8[i*3+2];
        // Print out the values for debugging.
        // Serial.print("R: ");
        // Serial.println(displayMemoryPtrU8[i*3]);
        // Serial.print("G: ");
        // Serial.println(displayMemoryPtrU8[i*3+1]);
        // Serial.print("B: ");
        // Serial.println(displayMemoryPtrU8[i*3+2]);
    }

    // Check if the total brightness exceeds the max.
    float totalBrightnessMilliamps = ((float) totalBrightness)/255.0 * MILLIAMPS_PER_COLOR;
    // Serial.print("Total brightness: ");
    // Serial.println(totalBrightnessMilliamps);
    if (totalBrightnessMilliamps > MAX_TOTAL_MILLIAMPS){
        // If it does, reduce the brightness of all pixels by the same amount.
        float brightnessReduction = MAX_TOTAL_MILLIAMPS / totalBrightnessMilliamps;
        for (int i=0; i < leds.numPixels(); i++) {
            displayMemoryPtrU8[i*3] *= brightnessReduction;
            displayMemoryPtrU8[i*3+1] *= brightnessReduction;
            displayMemoryPtrU8[i*3+2] *= brightnessReduction;
        }
    }

}
*/
