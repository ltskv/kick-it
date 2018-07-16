# Kicker project

## Prerequisites

1. (L)ubuntu 14.04
2. Git installed:

```sh
sudo apt install git -y 
```

## How to start working

1. Install the software: [instructions](
http://doc.aldebaran.com/2-1/dev/python/install_guide.html)

2. Check if NAOQi binding for Python works by launching Python and running there
`from naoqi import ALProxy`. The installation was successful if it imports
without errors. You can finish Python with `ctrl-d` then.

## What's inside?

* `__main__.py` - The script containing the state machine.
* `striker.py` - The class with high lever behaviors, e.g. aligning to ball.
* `movements.py` - Convenience classes for moving robot. Also kick is
implemented here.
* `finders.py` - Classes for Ball, Goal and Field detection.
* `imagereaders.py` - Convenience classes for capturing video input from
various sources.

**More documentation as well as the detailed report will be available later.**
