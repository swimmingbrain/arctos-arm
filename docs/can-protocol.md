# MKS SERVO42D / SERVO57D over CAN

What `arctos.mks` implements, condensed from the MKS manual. Standard 11 bit
frames, the CAN id is the driver id, the payload is

```
[command, data..., crc]      crc = (id + command + data bytes) & 0xFF
```

Replies use the same id and start with the same command byte. Most replies
carry a status byte: `1` ok, `0` failed. Positions are encoder counts,
16384 per motor revolution.

## Commands used by the library

| Byte | Name | Payload | Reply |
|---|---|---|---|
| 0x31 | read encoder | - | int48 accumulated counts |
| 0x32 | read speed | - | int16 rpm |
| 0x34 | read io | - | bit 0 IN_1, bit 1 IN_2, bit 2 OUT_1, bit 3 OUT_2 |
| 0x82 | set work mode | uint8 mode | status |
| 0x83 | set current | uint16 mA | status |
| 0x90 | set home params | trigger level, direction, uint16 rpm, end limit, no limit | status |
| 0x91 | go home | - | status |
| 0x92 | set zero | - | status |
| 0x9E | limit remap | 0/1 | status |
| 0xF1 | query status | - | 0 error, 1 stopped, 2 accelerating, 3 decelerating, 4 full speed, 5 homing |
| 0xF3 | enable | 0/1 | status |
| 0xF5 | move absolute | uint16 rpm, uint8 acc, int24 counts | 0 fail, 1 starting, 2 complete, 3 limit |
| 0xF4 | move relative | uint16 rpm, uint8 acc, int24 counts | as above |
| 0xF6 | speed mode | dir bit + 12 bit rpm, uint8 acc | status |
| 0xF7 | stop | - | status |

## Work modes

| Value | Mode | CAN motion commands |
|---|---|---|
| 0 | CR_OPEN | no |
| 1 | CR_CLOSE | no |
| 2 | CR_vFOC | no (factory default) |
| 3 | SR_OPEN | yes |
| 4 | SR_CLOSE | yes |
| 5 | SR_vFOC | yes, this is what the library expects |

The `CR` modes take pulse and direction on the input pins, the `SR` modes
take commands over CAN. In a `CR` mode the driver still answers to reads,
which is why `scan` can look fine while nothing moves.
