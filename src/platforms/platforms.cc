#include "platforms.h"
#include <config.h>

IO_CREATE_INSTANCE_OF(
	IWiFiPlatform,
	WiFiPlatform,
	{
		.ssid = CONFIG_WIFI_SSID,
		.password = CONFIG_WIFI_PASSWORD,
		.hostname = CONFIG_DEVICE_NAME,
		.startDelayMs = CONFIG_WIFI_START_DELAY
	}
);

IO_CREATE_INSTANCE_OF(
	ILightPlatform,
	LightPlatform,
	{
		.ledCount = CONFIG_LIGHT_LED_COUNT,
		.brightness = CONFIG_LIGHT_BRIGHTNESS_INITIAL,
		.colorCorrection = CONFIG_LIGHT_COLOR_CORRECTION,
        .temperatureInitial = CONFIG_LIGHT_COLOR_MIREDS_INITIAL,
        .temperatureCold = CONFIG_LIGHT_COLOR_MIREDS_COLD,
        .temperatureWarm = CONFIG_LIGHT_COLOR_MIREDS_WARM,
		.transitionMs = CONFIG_LIGHT_TRANSITION_COLOR
	}
);
