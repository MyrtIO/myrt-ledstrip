#include "fire_effect.h"
#include <LightComposer/math/scale.h>

const uint8_t kFireEffectCooling = 55;
const uint8_t kFireEffectSparking = 120;
const uint8_t kFireEffectInterval = 15;

const char* FireEffect::getName() {
	return "fire";
}

bool FireEffect::handleFrame(FireEffectState& state, IPixels& pixels) {
	if (!frameReady_.finished()) {
		return false;
	}

	// Step 1. Cool down every cell a little
	for (int i = 0; i < pixels.count(); i++) {
		cooldown_ = random(0, ((kFireEffectCooling * 10) / pixels.count()) + 2);

		if(cooldown_ > heat_[i]) {
			heat_[i] = 0;
		} else {
			heat_[i] = heat_[i] - cooldown_;
		}
	}

  // Step 2. Heat from each cell drifts 'up' and diffuses a little
  for (int k = pixels.count() - 1; k >= 2; k--) {
    heat_[k] = (heat_[k - 1] + heat_[k - 2] + heat_[k - 2]) / 3;
  }

  // Step 3. Randomly ignite new 'sparks' near the bottom
  if (random(255) < kFireEffectSparking) {
    int y = random(7);
    heat_[y] = heat_[y] + random(160,255);
  }

  // Step 4. Convert heat to LED colors
  for (int j = 0; j < pixels.count(); j++) {
	 // Scale 'heat' down from 0-255 to 0-191
	byte t192 = round((heat_[j]/255.0)*191);

	// calculate ramp up from
	byte heatRamp = t192 & 0x3F; // 0..63
	heatRamp <<= 2; // scale up to 0..252

	// figure out which third of the spectrum we're in:
	if( t192 > 0x80) {                     // hottest
		pixels.set(RGBColor(255, 255, heatRamp), j);
	} else if( t192 > 0x40 ) {             // middle
		pixels.set(RGBColor(255, heatRamp, 0), j);
	} else {                               // coolest
		pixels.set(RGBColor(heatRamp, 0, 0), j);
	}
  }

  frameReady_.start(kFireEffectInterval);
  return true;
}

void FireEffect::onColorUpdate(FireEffectState& state) {
	state.currentColor = state.targetColor;
}

FireEffect FireFx;
