# The MIT License (MIT)
#
# Copyright (c) 2018 Brent Rubell for Adafruit
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
"""
`ttn_eu.py`
======================================================
The Things Network Frequency Plans - EU863
* Author(s): Brent Rubell
"""
TTN_FREQS = {0: (0xd9, 0x06, 0x8b), # 868.1 MHz
             1: (0xd9, 0x13, 0x58), # 868.3 MHz
             2: (0xd9, 0x20, 0x24), # 868.5 MHz
             3: (0xd8, 0xc6, 0x8b), # 867.1 MHz
             4: (0xd8, 0xd3, 0x58), # 867.3 MHz
             5: (0xd8, 0xe0, 0x24), # 867.5 MHz
             6: (0xd8, 0xec, 0xf1), # 867.7 MHz
             7: (0xd8, 0xf9, 0xbe)} # 867.9 MHz


# PRV - Mais preciso
# 0   868100000   14222950.4      D90666
# 1   868300000   14226227.2      D91333
# 2   868500000   14229504        D92000
# 3   867100000   14206566.4      D8C666
# 4   867300000   14209843.2      D8D333
# 5   867500000   14213120        D8E000
# 6   867700000   14216396.8      D8ECCC
# 7   867900000   14219673.6      D8F999
