#include "boot_controller.h"
#include <MyrtIO/logging/logger.h>

const char* kBootControllerName = "Boot";

io::Logger connLog(kBootControllerName);

void BootController::setup() {
	firstConnect_ = true;
}

void BootController::loop() {
	if (!firstConnect_) {
		return;
	}
    if (!wifi_->connected()) {
        return;
    }
    if (!animationStarted_) {
        animationStarted_ = true;
        animationDelay_.start(100);
        return;
    }
    firstConnect_ = false;
    light_->setBrightness(connectedBrightness_);
}

const char* BootController::getName() {
	return kBootControllerName;
}
