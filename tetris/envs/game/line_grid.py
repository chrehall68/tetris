import pygame
from typing import Optional
from tetris.envs.game.constants import *


class LineGrid:
    def __init__(
        self,
        screen: pygame.Surface,
        color: Optional[tuple] = WHITE,
        render_mode: Optional[str] = None,
    ):
        self.screen = screen
        self.color = color
        self.render_mode = render_mode
        if self.render_mode == "human":
            pygame.init()

    def draw(self):
        assert self.render_mode == "human"
        # vertical lines
        for i in range(1, PLAYER_GRID_DIMENSIONS[0]):
            pygame.draw.line(
                self.screen,
                self.color,
                (i * BLOCK_SIZE + (i - 1) * LINE_SIZE, 0),
                (i * BLOCK_SIZE + (i - 1) * LINE_SIZE, PLAYER_DIMENSIONS[1]),
            )

        # horizontal lines
        for i in range(1, PLAYER_GRID_DIMENSIONS[1]):
            pygame.draw.line(
                self.screen,
                self.color,
                (0, i * BLOCK_SIZE + (i - 1) * LINE_SIZE),
                (PLAYER_DIMENSIONS[0], i * BLOCK_SIZE + (i - 1) * LINE_SIZE),
            )
