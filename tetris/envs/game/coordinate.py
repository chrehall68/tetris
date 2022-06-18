from typing import Optional, Union


class Coordinate:
    def __init__(self, x: Optional[int] = 0, y: Optional[int] = 0) -> None:
        self.x = x
        self.y = y

    def __floordiv__(self, num: Union[int, float]):
        return Coordinate(self.x // num, self.y // num)

    def __add__(self, o):
        if type(o) == Coordinate:
            return Coordinate(self.x + o.x, self.y + o.y)

    def __sub__(self, o):
        if type(o) == Coordinate:
            return Coordinate(self.x - o.x, self.y - o.y)

    def __iadd__(self, o):
        if type(o) == Coordinate:
            self.x += o.x
            self.y += o.y
            return self

    def __str__(self):
        return f"({self.x}, {self.y})"

    def __repr__(self):
        return str(self)

    def __mul__(self, o):
        if type(o) == int:
            return Coordinate(self.x * o, self.y * o)
