#pragma once

#include <PubSubServer.h>

void registerLightTopics(PubSubServer* server);
void registerLogTopics(PubSubServer* server, Stream* stream);
