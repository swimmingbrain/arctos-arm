# Configuration

Three yaml files, all in one folder:

| File | Content | Written by |
|---|---|---|
| `robot.yaml` | everything about the hardware | you |
| `poses.yaml` | taught joint poses, degrees | `arctos teach` |
| `offsets.yaml` | zero offset per joint, degrees | `arctos calibrate` |

The folder is found in this order: `--config` on the command line (a folder
or the robot.yaml itself), the environment variable `ARCTOS_CONFIG`, then
`./config`. If none of them has a robot.yaml, the default that ships inside the
package is used and poses/offsets are stored in `./config`. `arctos init`
copies that default so you can edit it.

## robot.yaml

### can

```yaml
can:
  interface: slcan          # slcan (CANable on USB) or socketcan
  channel: /dev/ttyACM0     # can0 for socketcan, COM5 on windows
  bitrate: 500000
  timeout: 0.5              # seconds to wait for a reply
  send_gap: 0.001           # pause between frames
```

Anything python-can supports works as `interface`. The simulation ignores
this section and opens a virtual bus.
