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
