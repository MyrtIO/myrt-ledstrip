#pragma once

#include <PubSubServer.h>

#define MQTT_TOPICS_PREFIX "myrt/ledstrip"

void registerLightTopics(PubSubServer* server);
void registerLogTopics(PubSubServer* server, Stream* stream);
