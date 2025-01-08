#pragma once

#include <MyrtIO/device/di.h>

#include "light/light_platform.h"
#include "wifi/wifi_platform.h"

IO_PROVIDE_IMPLEMENTATION(IWiFiPlatform);
IO_PROVIDE_IMPLEMENTATION(ILightPlatform);
