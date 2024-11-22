#include <MyrtIO/device/device.h>
#include "controllers/controllers.h"
#include "platforms/platforms.h"

io::Device strip("LEDStrip");

void setup() {
	// Enable MQTT logging
	auto mqttController = IO_INJECT_INSTANCE(MQTTController);
	io::Logger::setOutput(mqttController->logStream());

	strip.setup()
		// Add platforms
		.registerPlatform(IO_INJECT_UNIT(IWiFiPlatform))
		.registerPlatform(IO_INJECT_UNIT(ILightPlatform))
		// Add controllers
		.registerController(IO_INJECT_UNIT(BootController))
		.registerController(IO_INJECT_UNIT(MQTTController))
		.registerController(IO_INJECT_UNIT(OTAController));

	strip.log().print("initialized");
}

void loop() {
	strip.loop();
}
