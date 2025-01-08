#pragma once

#include <Attotime.h>
#include <MyrtIO/device/unit.h>
#include <platforms/platforms.h>

class BootController : public io::Unit {
  public:
	BootController(uint8_t connectedBrightness)
        : connectedBrightness_(connectedBrightness) {};
	void setup() override;
	void loop() override;
	const char* getName() override;

  private:
	uint8_t connectedBrightness_;
	bool firstConnect_;
    bool animationStarted_ = false;
    Timer animationDelay_;
	ILightPlatform* light_ = IO_INJECT(ILightPlatform);
	IWiFiPlatform* wifi_ = IO_INJECT(IWiFiPlatform);
};
