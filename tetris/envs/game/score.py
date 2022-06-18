from typing import Optional
import pygame
from tetris.envs.game.constants import *


class Score:
    """
    Auto clears the screen, so no need to clear it
    """

    def __init__(
        self, screen: pygame.Surface, render_mode: Optional[str] = None
    ) -> None:
        self.screen = screen
        self.score = 0
        self.render_mode = render_mode
        if self.render_mode == "human":
            pygame.init()
            pygame.font.init()

            self.font = pygame.font.SysFont("Comic Sans", TEXT_SIZE)

    def __iadd__(self, o):
        self.score += o

    def draw(self):
        assert self.render_mode == "human"
        self.screen.fill(BG_COLOR)
        self.screen.blit(self.font.render(f"Score: {self.score}", True, WHITE), (0, 0))
