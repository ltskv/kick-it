# Kicker project

## Prerequisites

1. (L)ubuntu 14.04
2. Git installed:

```sh
sudo apt install git -y 
```

## How to start working

### To run code on the laptop

1. Install Python and Python NAOqi SDK: [instructions](
http://doc.aldebaran.com/2-1/dev/python/install_guide.html)

2. Check if NAOQi binding for Python works by launching Python and running there
`from naoqi import ALProxy`. The installation was successful if it imports
without errors. You can finish Python with `ctrl-d` then.

3. Go to the project directory and run:

```sh
python -m pykick
```

This will launch the striker state machine, which should work if colors are
calibrated correctly.

4. To run the scripts from the project other than the main one, do this from
the project directory:

```sh
python -m pykick.[file_name_without_.py]
```

### To run code on the robot

1. Create a folder named `pykick` on the robot.

2. Copy the files from the project's `pykick` folder into `pykick` on the
robot.

3. ssh to the robot, go to the directory containing the `pykick` folder and run
`python -m pykick` (the same as on the laptop).

## What's inside?

* `__main__.py` - The script containing the state machine.
* `copyfiles.sh` - Script for convenient copying of the project files to the
robot (IP is hard-coded, so use with caution).
* `nao_defaults.json` - The settings such as color HSV values.
* `colorpicker.py` - Program for calibrating the colors. Run
`python -m pykick.colorpicker -h` to see how to use it.
* `detection_demo.py` - Program to check how good the robot can detect objects
with the current color settings.
* `striker.py` - The class with high lever behaviors, e.g. aligning to ball.
* `movements.py` - Convenience classes for moving robot. Also kick is
implemented here.
* `finders.py` - Classes for Ball, Goal and Field detection.
* `imagereaders.py` - Convenience classes for capturing video input from
various sources.

**More documentation as well as the detailed report will be available later.**
