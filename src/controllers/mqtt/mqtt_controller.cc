#include "mqtt_controller.h"
#include <MyrtIO/logging/logger.h>

const char* kMQTTName = "MQTT";

io::Logger mqttLog(kMQTTName);

const char* MQTTController::getName() {
	return kMQTTName;
}

void MQTTController::setup() {
    mqttLog.print("registering topics");
	registerLightTopics(&server_);
	registerLogTopics(&server_, logStream());
    mqttLog.print("starting server");
	server_.start(params_.host, params_.port);
}

void MQTTController::loop() {
    if (!initialized_) {
        if (!wifi_->connected()) {
            return;
        }
        initialized_ = true;
        mqttLog.print("listening to mqtt");
    }
	server_.loop();
}

void MQTTController::onConnect() {
	mqttLog.print("connected");
}

void MQTTController::onDisconnect() {
	mqttLog.print("disconnected");
}

void MQTTController::onMessage(char* topic, uint8_t* payload, uint16_t length) {
#ifdef IO_DEBUG
	mqttLog.build()
		.append("message received: ")
		.append(topic)
		.append(" - ")
		.append(length)
		.append(" bytes");
	mqttLog.flush();
#endif
}
