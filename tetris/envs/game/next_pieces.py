from typing import Optional
import pygame
from tetris.envs.game.constants import *
from tetris.envs.game.piece import *
import random


class NextPieces:
    """
    Class for representing the next pieces
    Auto clears the screen, so no need to do clear the screen
    """

    def __init__(
        self, screen: pygame.Surface, render_mode: Optional[str] = None
    ) -> None:
        self.screen = screen
        self.piece_options = (LPiece, JPiece, IPiece, SPiece, ZPiece, TPiece, OPiece)
        self.next_pieces = [random.choice(self.piece_options) for i in range(3)]
        self.render_mode = render_mode
        if self.render_mode == "human" or self.render_mode == "rgb-array":
            pygame.init()
            pygame.font.init()
            self.font = pygame.font.SysFont("Comic Sans", TEXT_SIZE)

    def step(self) -> Piece:
        ret = self.next_pieces.pop(0)
        self.next_pieces.append(random.choice(self.piece_options))
        return ret

    def draw(self):
        assert self.render_mode == "human" or self.render_mode == "rgb-array"
        self.screen.fill(BLACK)
        self.screen.blit(self.font.render("Next:", True, TEXT_COLOR), (0, 0))
        for piece, idx in zip(self.next_pieces, [i for i in range(3)]):
            piece(
                self.screen,
                (
                    SPACE_SIZE,
                    NEXT_PIECES_LABEL_DIMENSIONS[1] + (3 * idx + 1) * SPACE_SIZE,
                ),
                render_mode=self.render_mode,
            ).draw()
