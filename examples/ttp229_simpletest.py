# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2024 Cooper Dalrymple
#
# SPDX-License-Identifier: Unlicense
import time

import board

import ttp229

ttp = ttp229.TTP229(board.GP14, board.GP15, invert_clk=True)

ttp.on_press = lambda i: print(f"Press: {i:d}")
ttp.on_release = lambda i: print(f"Release: {i:d}")

while True:
    ttp.update()
