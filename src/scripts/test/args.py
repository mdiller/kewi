import kewi.args
from enum import Enum

class Color(Enum):
    RED = 1
    GREEN = 2
    BLUE = 3

ARG_name: str
ARG_thing: Color
ARG_number: int = 0
kewi.ctx.init()

print(f"Name: {ARG_name}")
print(f"Thing: {ARG_thing}")
print(f"Number: {ARG_number}")

