# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2024 Cooper Dalrymple
#
# SPDX-License-Identifier: MIT
"""
`ttp229`
================================================================================

TonTouch TTP229 hardware driver for CircuitPython.


* Author(s): Cooper Dalrymple

Implementation Notes
--------------------

**Hardware:**

* `HiLetgo TTP229 16 Channel Sensor Module:
  <https://www.amazon.com/HiLetgo-TTP229-Channel-Digital-Capacitive/dp/B01N1LZKIJ>`_

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://circuitpython.org/downloads
"""

# imports

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/dcooperdalrymple/CircuitPython_TTP229.git"

import array

from microcontroller import Pin
from micropython import const

try:
    import adafruit_pioasm
    import rp2pio
except ImportError:
    import digitalio

try:
    from typing import Callable
except ImportError:
    pass


class Mode:
    """Enum-like class representing the possible modes of the TTP229."""

    KEY_8 = const(0)

    KEY_16 = const(1)


class TTP229:
    on_press: Callable[[int], None] = None

    on_release: Callable[[int], None] = None

    def __init__(self, sdo: Pin, scl: Pin, mode: int = Mode.KEY_16, invert_clk: bool = False):
        self._data = array.array("H", [0, 0])
        self._mode = mode
        self._count = (mode + 1) * 8
        self._index = 0
        self._invert_clk = invert_clk

        if "rp2pio" in globals():
            clk_off = 1 if invert_clk else 0
            clk_on = 0 if invert_clk else 0
            clk_cnt = self._count - 1
            pioasm = f"""
.program read_ttp
    set pins, {clk_off}
.wrap_target
    set y, 3
tout_y:
    set x, 31
tout_x:
    nop [31]
    jmp x-- tout_x
    jmp y-- tout_y
    set x, {clk_cnt}
bitloop:
    set pins, {clk_on} [3]
    set pins, {clk_off} [1]
    in pins, 1
    jmp x-- bitloop
    push
.wrap
"""
            self._piosm = rp2pio.StateMachine(
                adafruit_pioasm.assemble(pioasm),
                frequency=2000000,  # 2MHz, cycle = 0.5us
                first_in_pin=sdo,
                in_pin_count=1,
                pull_in_pin_up=1,
                first_set_pin=scl,
                set_pin_count=1,
                initial_set_pin_state=clk_off,
                initial_set_pin_direction=1,
            )
            # Timing Details:
            # Clock Cycle (F_SCL) = 8 pio cycles = 4us = 250KHz
            # Word Cycle = 64us = ~15.6KHz
            # Delay (Tout) = 2ms
            # Frequency (T_resp) = 2064us = ~484.5Hz

        else:
            self._sdo = digitalio.DigitalInOut(sdo)
            self._sdo.direction = digitalio.Direction.INPUT
            self._sdo.pull = digitalio.Pull.UP

            self._scl = digitalio.DigitalInOut(scl)
            self._scl.direction = digitalio.Direction.OUTPUT

    def update(self) -> bool:
        if "rp2pio" in globals():
            if self._piosm.in_waiting <= 0:
                return False
            self._piosm.readinto(self._data, end=1)
        else:
            self._data[0] = 0
            self._scl.value = self._invert_clk
            for i in range(self._count):
                self._scl.value = not self._invert_clk
                if self._sdo.value:
                    self._data[0] |= 1 << i
                self._scl.value = self._invert_clk
            self._scl.value = not self._invert_clk

        for i in range(self._count):
            value = self._data[0] & (1 << i)
            if value != self._data[1] & (1 << i):
                if value and callable(self.on_press):
                    self.on_press(i)
                elif not value and callable(self.on_release):
                    self.on_release(i)
        self._data[1] = self._data[0]

        return True

    @property
    def data(self) -> int:
        return self._data[0]

    def __getitem__(self, index: int) -> bool:
        return bool(self._data[0] & (1 << (index % self._count)))

    def __len__(self):
        return self._count
