# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2024 Cooper Dalrymple
#
# SPDX-License-Identifier: Unlicense
import time

import board

import ttp229

ttp = ttp229.TTP229(board.GP14, board.GP15, invert_clk=True)

while True:
    if ttp.update():
        print(bin(ttp.data))
    time.sleep(0.1)
