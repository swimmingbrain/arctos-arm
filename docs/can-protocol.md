# MKS SERVO42D / SERVO57D over CAN

What `arctos.mks` implements, condensed from the MKS manual. Standard 11 bit
frames, the CAN id is the driver id, the payload is

```
[command, data..., crc]      crc = (id + command + data bytes) & 0xFF
```

Replies use the same id and start with the same command byte. Most replies
carry a status byte: `1` ok, `0` failed. Positions are encoder counts,
16384 per motor revolution.
