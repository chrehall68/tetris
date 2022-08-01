from typing import Optional
import pygame
from tetris.envs.game.constants import *
from tetris.envs.game.base_piece import BasePiece
from tetris.envs.game.coordinate import Coordinate


class Holder:
    """
    Class for the piece that is held
    Auto clears screens, so no need to clear it.
    """

    def __init__(self, screen: pygame.Surface, render_mode: Optional[str] = None):
        self.screen = screen
        self.piece_screen = pygame.Surface(HOLDER_BOX_DIMENSIONS)
        self.held_piece = None
        self.render_mode = render_mode
        if self.render_mode == "human" or self.render_mode == "rgb-array":
            pygame.init()
            pygame.font.init()
            self.font = pygame.font.SysFont("Comic Sans", TEXT_SIZE)

    def swap(self, piece: BasePiece):
        temp = self.held_piece
        if temp is not None:
            temp.top_left = Coordinate(BLOCK_START[0], BLOCK_START[1])
            temp.set_screen(piece.screen)
            temp._get_blocks()

        self.held_piece = piece
        self.held_piece.set_screen(self.piece_screen)
        self.held_piece.top_left = Coordinate(SPACE_SIZE, SPACE_SIZE)
        self.held_piece._get_blocks()

        return temp

    def draw(self):
        assert self.render_mode == "human" or self.render_mode == "rgb-array"
        self.screen.fill(BG_COLOR)
        self.piece_screen.fill(BG_COLOR)

        self.screen.blit(self.font.render("Hold:", True, TEXT_COLOR), (0, 0))
        if self.held_piece is not None:
            self.held_piece.draw()
        self.screen.blit(self.piece_screen, (0, HOLDER_LABEL_DIMENSIONS[1]))
