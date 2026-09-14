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
