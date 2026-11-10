"""SCUMM-v6 Actor face directions expressed in native angle degrees.

ScummC's NORTH/EAST/SOUTH/WEST constants are old 0..3 direction IDs.
ScummVM's v6 actor FACE opcode instead consumes a 0..359 degree angle
(actor.cpp setDirection; util.cpp oldDirToNewDir).
"""

ACTOR_FACING_ANGLES = {"N": 0, "E": 90, "S": 180, "W": 270}


def actor_facing_angle(direction: str) -> int:
    return ACTOR_FACING_ANGLES[direction]
