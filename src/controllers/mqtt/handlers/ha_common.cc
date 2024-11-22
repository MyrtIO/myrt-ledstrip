#include "ha_common.h"
#include "topics.h"
#include <config.h>

// const HomeAssistant::DeviceConfig deviceConfig();
HomeAssistant::Device haDesk = HomeAssistant::Device({
    .name = CONFIG_DEVICE_NAME,
    .id = CONFIG_DEVICE_ID,
    .mqttNamespace = MQTT_TOPICS_PREFIX
});
char responseBuffer[MQTT_BUFFER_SIZE];
