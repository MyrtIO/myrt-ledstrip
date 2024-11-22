#include <PubSubServer.h>
#include <HomeAssistantJSON/light_entity.h>
#include <platforms/platforms.h>
#include <config.h>
#include "ha_common.h"

HomeAssistant::LightEntity lightEntity({
    .name = "Light",
	.identifier = "light",
	.icon = "mdi:led-strip-variant",
    .effects = nullptr,
    .effectCount = 0,
	.writable = true,
	.maxMireds = CONFIG_LIGHT_COLOR_MIREDS_WARM,
	.minMireds = CONFIG_LIGHT_COLOR_MIREDS_COLD
}, haDesk);

ILightPlatform* light;
HomeAssistant::LightState state;

bool isColorEquals(const HomeAssistant::RGBColor& ha, const RGBColor& platform) {
	return (ha.r == platform.r) && (ha.g == platform.g) && (ha.b == platform.b);
}

void reportLightConfig(PubSubClient* client) {
	lightEntity.serializeConfig(responseBuffer);
	client->publish(lightEntity.configTopic(), responseBuffer);
}

void reportLightState(PubSubClient* client) {
	state.enabled = light->getPower();
	state.colorTemp = light->getTemperature();
	state.effect = light->getEffect();
	state.brightness = light->getBrightness();
	auto currentColor = light->getColor();
	state.color = {
		.r = currentColor.r,
		.g = currentColor.g,
		.b = currentColor.b
	};
	switch (light->getMode()) {
	case LightMode::RGBMode:
		state.colorMode = HomeAssistant::ColorMode::RGBMode;
		break;
	case LightMode::WhiteMode:
		state.colorMode = HomeAssistant::ColorMode::ColorTempMode;
		break;
	}
	lightEntity.serializeValue(responseBuffer, state);
	client->publish(lightEntity.stateTopic(), responseBuffer);
}

void updateLightState(PubSubClient* client, byte* payload, uint length) {
	lightEntity.parseValue(state, payload);
	auto enabled = light->getPower();
	auto brightness = light->getBrightness();
	auto colorTemp = light->getTemperature();
	auto color = light->getColor();

	if (state.enabled != enabled) {
		light->setPower(state.enabled);
	} else if (brightness != state.brightness && state.brightness != 0) {
		light->setBrightness(state.brightness);
	}
	if (state.effect != nullptr) {
		light->setEffect(state.effect);
	}
	if (!isColorEquals(state.color, color) &&
		!isColorEquals(state.color, RGBColor::Black)) {
		light->setColor(
			RGBColor(state.color.r, state.color.g, state.color.b)
		);
	} else if (state.colorTemp != 0) {
		light->setColorTemperature(state.colorTemp);
	}
	reportLightState(client);
}

void registerLightTopics(PubSubServer* server) {
    for (int i = 0; i < MQTT_BUFFER_SIZE; i++) {
        responseBuffer[i] = 0;
    }
	light = IO_INJECT(ILightPlatform);
	lightEntity.setEffects(light->effects(), light->effectCount());
	server
		->report(reportLightConfig, MQTT_CONFIG_REPORT_INTERVAL)
		->report(reportLightState, MQTT_STATE_REPORT_INTERVAL)
		->on(lightEntity.commandTopic(), updateLightState);
}
