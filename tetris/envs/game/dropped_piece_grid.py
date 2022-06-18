from typing import Optional
import pygame
from tetris.envs.game.constants import *
from tetris.envs.game.base_piece import BasePiece
from tetris.envs.game.coordinate import Coordinate
from tetris.envs.game.score import Score
import numpy


class DroppedPieceGrid:
    def __init__(self, score_keeper: Score, render_mode: Optional[str] = None) -> None:
        self.score_keeper = score_keeper
        self.used_spaces = numpy.array(
            [
                [None for x in range(PLAYER_GRID_DIMENSIONS[0])]
                for y in range(PLAYER_GRID_DIMENSIONS[1])
            ]
        )
        self.height = 0
        self.past_height = 0
        self.delta_h = 0

        self.lines_just_cleared = 0
        self.last_piece_ending_height = 0
        self.last_piece_spaces = []

        self.render_mode = render_mode
        if self.render_mode == "human":
            pygame.init()

    def contains_piece(self, piece: BasePiece, **kwargs):
        """
        @brief checks if a piece is in the grid
        @param piece - the piece to be checked
        @param kwargs - valid options are: top_left, arrangement
        """
        if "top_left" in kwargs:
            true_coord = kwargs["top_left"] // SPACE_SIZE
        else:
            true_coord = piece.top_left // SPACE_SIZE

        if "arrangement" in kwargs:
            true_arrangement = kwargs["arrangement"]
        else:
            true_arrangement = piece.arrangement

        try:
            return any(
                [
                    self[Coordinate(true_coord.x + coord[0], true_coord.y + coord[1])]
                    for coord in true_arrangement
                ]
            )
        except IndexError:
            return True

    def __contains__(self, coord: Coordinate) -> bool:
        true_coord = coord // SPACE_SIZE
        return (
            self[Coordinate(true_coord.x + coord[0], true_coord.y + coord[1])]
            is not None
        )

    def __getitem__(self, coord: Coordinate) -> bool:
        return (
            coord.x < 0 or coord.y < 0 or self.used_spaces[coord.y, coord.x] is not None
        )

    def __iadd__(self, piece: BasePiece):
        if piece is not None:
            max_height = self._add_to_grid(piece)

            # check if any rows have been cleared
            rows_cleared = 0
            for y in range(len(self.used_spaces)):
                if all(self.used_spaces[y]):
                    # row is all filled:
                    rows_cleared += 1

                    # move everything down
                    self.used_spaces[1 : y + 1] = self.used_spaces[0:y]
                    for row in self.used_spaces[1 : y + 1]:
                        for block in row:
                            if block is not None:
                                block.set_top_left(
                                    Coordinate(
                                        block.top_left.x, block.top_left.y + SPACE_SIZE
                                    )
                                )

                    # clear the top row
                    self.used_spaces[0] = numpy.array(
                        [None] * PLAYER_GRID_DIMENSIONS[0]
                    )

            # update score
            self.score_keeper.score += LINE_CLEAR_SCORES[rows_cleared]

            # update internals
            self.lines_just_cleared = rows_cleared
            self.past_height = self.height
            self.height = self._get_height()
            self.delta_h = self.height - self.past_height
            self.last_piece_ending_height = max_height + 1  # +1 so that 19 -> 20

        return self

    def draw(self):
        assert self.render_mode == "human"
        for row in self.used_spaces:
            for block in row:
                if block is not None:
                    block.draw()

    @property
    def numeric_used_spaces(self):
        ret = []
        for row in self.used_spaces:
            ret.append(tuple([1 if row[x] is not None else 0 for x in range(len(row))]))
        return tuple(ret)

    def _get_height(self):
        """
        Returns the height of the grid
        * Range is from 0 - 20
        """
        height = 20
        for y in range(len(self.used_spaces), 0, -1):
            if all([cell is None for cell in self.used_spaces[y - 1]]):
                height = 20 - y
                break
        return height

    def _add_to_grid(self, piece: BasePiece) -> int:
        """
        Returns the max height of the pieces
        """
        max_height = 0
        if piece is not None:
            self.last_piece_spaces = []

            max_height = (piece.blocks[0].top_left // SPACE_SIZE).y
            for block in piece.blocks:
                temp = block.top_left // SPACE_SIZE
                self.used_spaces[temp.y, temp.x] = block
                self.last_piece_spaces.append((temp.y, temp.x))
                max_height = max(temp.y, max_height)

        return max_height

    def _undo_last_drop(self):
        for space in self.last_piece_spaces:
            self.used_spaces[space] = None

    def simulate_drop(
        self, piece: BasePiece, cur_ul: Optional[Coordinate] = None
    ) -> int:
        if cur_ul is None:
            cur_ul = piece.top_left
        prev_top_left = piece.top_left

        piece.set_top_left(cur_ul)
        self._add_to_grid(piece)
        ret = self._get_height() - self.height
        self._undo_last_drop()
        piece.set_top_left(prev_top_left)
        return ret
