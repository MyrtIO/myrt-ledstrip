BOARD_TTY = /dev/cu.usbserial-0001
BAUD_RATE = 115200

.PHONY: configure
configure:
	@pio init --ide vscode
	@make build

.PHONY: build
build: include/config.h
	@pio run

.PHONY: deploy
flash: include/config.h
	@pio run --target clean
	@pio run -t upload --upload-port $(BOARD_TTY) -e release

.PHONY: flash-debug
flash-debug: include/config.h
	@pio run -t upload --upload-port $(BOARD_TTY) -e debug
	@sleep 1
	@make monitor

.PHONY: ota
ota: include/config.h
	@pio run -e release
	@python scripts/espota.py \
			-i 192.168.1.145 \
			-p 3200 \
			-f .pio/build/release/firmware.bin

.PHONY: monitor
monitor:
	pio device monitor -p $(BOARD_TTY) --baud $(BAUD_RATE)

.PHONY: format
format:
	@astyle --project=.astylerc -n \
		-r 'src/*.cc' \
		-r 'src/*.h' \
		-r 'lib/*.cc' \
		-r 'lib/*.h' \
		-r 'include/*.h'

.PHONY: include/config.h
include/config.h:
	@python .pio/libdeps/release/MyrtIO/tools/configgen/configgen.py \
		src/config.yaml \
		include/config.h