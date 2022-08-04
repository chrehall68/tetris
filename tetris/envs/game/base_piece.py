import pygame
from typing import Tuple, Union, Optional
from tetris.envs.game.coordinate import Coordinate
from tetris.envs.game.constants import *


class Block:
    """
    Class used to represent the individual blocks that pieces are made up of
    """

    def __init__(
        self,
        screen: pygame.Surface,
        color: tuple,
        top_left: Union[tuple, Coordinate],
    ) -> None:
        self.screen = screen
        self.color = color

        self.top_left = None
        if type(top_left) == tuple:
            self.top_left = Coordinate(top_left[0], top_left[1])
        else:
            self.top_left = top_left

    def set_top_left(self, new_top_left):
        self.top_left = new_top_left

    def draw(self):
        pygame.draw.rect(
            self.screen,
            self.color,
            pygame.Rect(self.top_left.x, self.top_left.y, BLOCK_SIZE, BLOCK_SIZE),
        )

    def __repr__(self):
        return "B"


class BasePiece:
    """
    Base class for pieces.
    Used to avoid undefined errors.
    """

    def __init__(
        self,
        screen: pygame.Surface,
        arrangement: tuple,
        color: tuple,
        top_left: Union[tuple, Coordinate],
        render_mode: Optional[str] = None,
    ):
        self.screen = screen
        self.arrangement = list(arrangement)
        self.color = color

        self.top_left = None
        if type(top_left) == Coordinate:
            self.top_left = top_left
        else:
            self.top_left = Coordinate(top_left[0], top_left[1])

        self.render_mode = render_mode
        if self.render_mode == "human":
            pygame.init()

        self._get_blocks()

    def _get_blocks(self):
        self.blocks = [
            Block(
                self.screen,
                self.color,
                (
                    self.top_left.x + coord[0] * SPACE_SIZE,
                    self.top_left.y + coord[1] * SPACE_SIZE,
                ),
            )
            for coord in self.arrangement
        ]

    def set_screen(self, screen: pygame.Surface):
        for block in self.blocks:
            block.screen = screen
        self.screen = screen

    def draw(self):
        assert self.render_mode == "human" or self.render_mode == "rgb-array"
        for block in self.blocks:
            block.draw()

    def move(self, event: Optional[pygame.event.Event] = None) -> bool:
        """
        Attempts to move the piece.
        Returns True on success, False on failure to move the piece
        """
        pass

    def move_down(self) -> bool:
        """
        Returns True if it succeeded in moving down, False otherwise
        """
        pass

    def rotate_left(self, cur_top_left: Coordinate):
        pass

    def rotate_right(self, cur_top_left: Coordinate):
        pass

    def set_top_left(self, new_top_left: Coordinate):
        self.top_left = new_top_left
        self._get_blocks()

    def clone(self):
        raise NotImplementedError("Must be done in a subclass")
