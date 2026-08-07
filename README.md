# arctos-arm

Python library, command line tool and ROS 2 packages for the
[Arctos](https://arctosrobotics.com) robot arm with MKS SERVO42D / SERVO57D
closed loop stepper drivers on a CAN bus.

It talks to the drivers directly over CAN, knows about gear ratios, the wrist
differential, joint limits and homing offsets, does forward and inverse
kinematics, and ships a simulation so that everything also runs on a laptop
without the robot.
