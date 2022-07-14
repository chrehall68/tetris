import pygame
from typing import Optional, Union, Tuple
from tetris.envs.game.base_piece import BasePiece
from tetris.envs.game.coordinate import Coordinate
from tetris.envs.game.dropped_piece_grid import DroppedPieceGrid
from tetris.envs.game.constants import *
from tetris.envs.game.score import Score


class Piece(BasePiece):
    def __init__(
        self,
        screen: pygame.Surface,
        arrangement: tuple,
        color: tuple,
        top_left: tuple,
        dropped_piece_grid: Optional[DroppedPieceGrid] = None,
        rotate_center: tuple = None,
        score_keeper: Optional[Score] = None,
        render_mode: Optional[str] = None,
    ):
        super().__init__(screen, arrangement, color, top_left, render_mode)
        self._out = False
        self.dropped_piece_grid = dropped_piece_grid
        self.score_keeper = score_keeper
        self.rotate_center = rotate_center

    @property
    def out(self):
        return self._out

    def _rotate(
        self, cur_top_left: Coordinate, new_arrangement: Tuple[list], check_valid=True
    ) -> Coordinate:
        """
        Helper method that does the calculating and modifying of self.arrangement and self.rotate_center
        @Pre - self.rotate_center is not None
        """
        assert (
            self.rotate_center is not None
        ), "Can't rotate around nothing!!! Please provide a rotate_center"

        # get the absolute coordinate of the rotate center
        center_coord = Coordinate(
            cur_top_left.x + self.rotate_center[0] * SPACE_SIZE,
            cur_top_left.y + self.rotate_center[1] * SPACE_SIZE,
        )

        # the location of the top left, relative to the rotate center
        relative_top_left = min([coord[0] for coord in new_arrangement]), min(
            [coord[1] for coord in new_arrangement]
        )

        # get the new absolute top left
        new_top_left = Coordinate(
            center_coord.x + relative_top_left[0] * SPACE_SIZE,
            center_coord.y + relative_top_left[1] * SPACE_SIZE,
        )

        # the new rotate center, relative to the new top left
        new_center = -relative_top_left[0], -relative_top_left[1]

        # shift the arrangement to be back to being
        # relative to the top left
        for coord in new_arrangement:
            coord[0] -= relative_top_left[0]
            coord[1] -= relative_top_left[1]

        if check_valid:
            # try the rotate
            self.arrangement, actual_top_left, self.rotate_center = self._try_rotate(
                new_arrangement, cur_top_left, new_top_left, new_center
            )
        else:
            # assume that it is valid (because check_valid is False)
            self.arrangement, actual_top_left, self.rotate_center = (
                new_arrangement,
                new_top_left,
                new_center,
            )

        return actual_top_left

    def rotate_left(self, cur_top_left: Coordinate) -> Coordinate:
        """
        Modifies self.arrangement and self.rotate_center. DOES NOT modify self.top_left
        Instead, returns a coordinate that can be used as the new top left.
        """
        if self.rotate_center is not None:
            new_arrangement = []
            for coord in self.arrangement:
                new_arrangement.append(
                    [
                        coord[1] - self.rotate_center[1],
                        -(coord[0] - self.rotate_center[0]),
                    ]
                )

            return self._rotate(cur_top_left, new_arrangement)

        return cur_top_left

    def rotate_right(self, cur_top_left: Coordinate, check_valid=True) -> Coordinate:
        """
        Modifies self.arrangement and self.rotate_center. DOES NOT modify self.top_left
        Instead, returns a coordinate that can be used as the new top left.
        """
        if self.rotate_center is not None:
            new_arrangement = []
            for coord in self.arrangement:
                new_arrangement.append(
                    [
                        -(coord[1] - self.rotate_center[1]),
                        coord[0] - self.rotate_center[0],
                    ]
                )
            return self._rotate(cur_top_left, new_arrangement, check_valid)

        return cur_top_left

    def _try_move(
        self,
        cur_top_left: Coordinate,
        coord_to_add: Coordinate,
        moved_coord: Optional[Coordinate] = Coordinate(),
    ) -> Coordinate:
        """
        Attempts to do the move given. If it succeeds, the returned coordinate will reflect
        the move. If not, then the returned coordinate will be the same as the original.
        If a moved_coord is provided, then that will be modified to reflect the delta pos
        """
        temp = cur_top_left + coord_to_add
        if not self.dropped_piece_grid.contains_piece(self, top_left=temp):
            moved_coord += coord_to_add
            return temp
        return cur_top_left

    def _try_hard_drop(
        self, cur_top_left: Coordinate, moved_coord: Optional[Coordinate] = Coordinate()
    ) -> Coordinate:
        """
        Attempts to hard drop the piece. If it succeeds, the returned coordinate will reflect
        the move. If not, then the returned coordinate will be the same as the original.
        If a moved_coord is provided, then that will be modified to reflect the delta pos
        """
        past = cur_top_left
        cur = cur_top_left
        cur = self._try_move(cur, Coordinate(0, SPACE_SIZE), moved_coord)
        while cur != past:
            past = cur
            cur = self._try_move(cur, Coordinate(0, SPACE_SIZE), moved_coord)
        return cur

    def _try_rotate(
        self,
        arrangement: Union[list, tuple],
        old_top_left: Coordinate,
        new_top_left: Coordinate,
        new_center: tuple,
    ) -> Tuple[list, Coordinate]:
        """
        Attempts to do use the given arrangement.
        If it succeeds, it will return the arrangement and the new top left
        Else, it will return the old top left and the piece's original arrangement
        """
        if not self.dropped_piece_grid.contains_piece(
            self, top_left=new_top_left, arrangement=arrangement
        ):
            return arrangement, new_top_left, new_center
        return self.arrangement, old_top_left, self.rotate_center

    def move(
        self,
        keyInputs: Optional[Tuple[pygame.event.Event]] = None,
    ) -> bool:
        # valid move variables
        valid_move = True
        prev_arrangement = self.arrangement
        prev_rotate_center = self.rotate_center
        had_valid_key = False

        next_coordinate = self.top_left

        if keyInputs is not None:
            for event in keyInputs:
                if (event.type == pygame.KEYDOWN) and event.key in KEY_MAPPINGS:
                    had_valid_key = True

                    if (
                        KEY_MAPPINGS[event.key] == "nothing"
                        or KEY_MAPPINGS[event.key] == "hold"
                    ):
                        return True  # nothing and hold are valid moves.
                    if KEY_MAPPINGS[event.key] == "right":
                        next_coordinate = self._try_move(
                            next_coordinate, Coordinate(SPACE_SIZE, 0)
                        )
                    if KEY_MAPPINGS[event.key] == "left":
                        next_coordinate = self._try_move(
                            next_coordinate, Coordinate(-SPACE_SIZE, 0)
                        )
                    if KEY_MAPPINGS[event.key] == "soft drop":
                        next_coordinate = self._try_move(
                            next_coordinate, Coordinate(0, SPACE_SIZE)
                        )
                        # this should increase score by 1
                        if self.score_keeper is not None:
                            self.score_keeper.score += 1
                    if KEY_MAPPINGS[event.key] == "hard drop":
                        temp = Coordinate()
                        next_coordinate = self._try_hard_drop(next_coordinate, temp)

                        if self.score_keeper is not None:
                            # this should increase score by 2 * spaces_dropped
                            self.score_keeper.score += 2 * (temp // SPACE_SIZE).y
                        self._out = True

                    if KEY_MAPPINGS[event.key] == "spin right":
                        next_coordinate = self.rotate_right(next_coordinate)
                    if KEY_MAPPINGS[event.key] == "spin left":
                        next_coordinate = self.rotate_left(next_coordinate)

        if (
            had_valid_key
            and next_coordinate == self.top_left
            and prev_arrangement == self.arrangement
            and prev_rotate_center == self.rotate_center
        ):
            # if absolutely nothing changed
            # and it had valid keys,
            # it must've been an invalid move
            valid_move = False
        self.top_left = next_coordinate
        self._get_blocks()
        return valid_move

    def move_down(self) -> bool:
        old_top_left = self.top_left
        next_coordinate = self._try_move(self.top_left, Coordinate(0, SPACE_SIZE))
        self.top_left = next_coordinate
        return old_top_left != self.top_left

    def get_height(self) -> int:
        """
        Returns height IN SQUARES, NOT PIXELS
        """
        return max([lst[1] for lst in self.arrangement])

    def _get_best_ul(self) -> Tuple[Coordinate, int]:
        """
        Bases optimal piece based on minimized board delta h, maximized piece delta h
        """
        cur_ul = Coordinate()
        max_piece_delta_h = 0
        min_board_delta_h = 20

        best_pos = Coordinate()

        for x in range(PLAYER_GRID_DIMENSIONS[0]):
            for y in range(PLAYER_GRID_DIMENSIONS[1]):
                cur_ul = Coordinate(x, y) * SPACE_SIZE

                if self.dropped_piece_grid.contains_piece(self, top_left=cur_ul):
                    continue
                if not self.dropped_piece_grid.contains_piece(
                    self, top_left=Coordinate(cur_ul.x, cur_ul.y + SPACE_SIZE)
                ):
                    continue

                board_delta_h = self.dropped_piece_grid.simulate_drop(self, cur_ul)

                piece_delta_h = cur_ul.y // SPACE_SIZE + self.get_height()

                if (
                    board_delta_h < min_board_delta_h
                    and piece_delta_h > max_piece_delta_h
                ):
                    max_piece_delta_h = piece_delta_h
                    min_board_delta_h = board_delta_h
                    best_pos = cur_ul

        return best_pos, min_board_delta_h, max_piece_delta_h

    def get_best_position(self):
        """
        The best UL and the best arrangement

        Bases optimal piece based on minimized board delta h, maximized piece delta h,
        minimized piece height

        """
        best_arrangement = self.arrangement
        best_ul = Coordinate()
        max_piece_delta_h = 0
        min_board_delta_h = 20
        min_piece_height = 20

        for i in range(4):  # since there are at max distinct rotations
            self.rotate_right(Coordinate(), False)
            self._get_blocks()
            _, board_delta_h, piece_delta_h = self._get_best_ul()
            if (
                board_delta_h <= min_board_delta_h
                and piece_delta_h >= max_piece_delta_h
                and self.get_height() <= min_piece_height
            ):
                min_board_delta_h = board_delta_h
                max_piece_delta_h = piece_delta_h
                min_piece_height = self.get_height()

                best_arrangement = self.arrangement
                best_ul = _

        return best_ul, best_arrangement


class OPiece(Piece):
    def __init__(
        self,
        screen: pygame.Surface,
        top_left: tuple,
        dropped_piece_grid: Optional[DroppedPieceGrid] = None,
        score_keeper: Optional[Score] = None,
        render_mode: Optional[str] = None,
    ):
        super().__init__(
            screen,
            ((0, 0), (0, 1), (1, 0), (1, 1)),
            YELLOW,
            top_left,
            dropped_piece_grid,
            score_keeper=score_keeper,
            render_mode=render_mode,
        )


class ZPiece(Piece):
    def __init__(
        self,
        screen: pygame.Surface,
        top_left: tuple,
        dropped_piece_grid: Optional[DroppedPieceGrid] = None,
        score_keeper: Optional[Score] = None,
        render_mode: Optional[str] = None,
    ):
        super().__init__(
            screen,
            ((1, 0), (0, 1), (1, 1), (2, 0)),
            RED,
            top_left,
            dropped_piece_grid,
            (1, 1),
            score_keeper,
            render_mode,
        )


class SPiece(Piece):
    def __init__(
        self,
        screen: pygame.Surface,
        top_left: tuple,
        dropped_piece_grid: Optional[DroppedPieceGrid] = None,
        score_keeper: Optional[Score] = None,
        render_mode: Optional[str] = None,
    ):
        super().__init__(
            screen,
            ((0, 0), (1, 0), (1, 1), (2, 1)),
            GREEN,
            top_left,
            dropped_piece_grid,
            (1, 1),
            score_keeper,
            render_mode,
        )


class JPiece(Piece):
    def __init__(
        self,
        screen: pygame.Surface,
        top_left: tuple,
        dropped_piece_grid: Optional[DroppedPieceGrid] = None,
        score_keeper: Optional[Score] = None,
        render_mode: Optional[str] = None,
    ):
        super().__init__(
            screen,
            ((0, 0), (0, 1), (1, 1), (2, 1)),
            DARK_BLUE,
            top_left,
            dropped_piece_grid,
            (1, 1),
            score_keeper,
            render_mode,
        )


class LPiece(Piece):
    def __init__(
        self,
        screen: pygame.Surface,
        top_left: tuple,
        dropped_piece_grid: Optional[DroppedPieceGrid] = None,
        score_keeper: Optional[Score] = None,
        render_mode: Optional[str] = None,
    ):
        super().__init__(
            screen,
            ((0, 0), (0, 1), (1, 0), (2, 0)),
            ORANGE,
            top_left,
            dropped_piece_grid,
            (1, 0),
            score_keeper,
            render_mode,
        )


class IPiece(Piece):
    def __init__(
        self,
        screen: pygame.Surface,
        top_left: tuple,
        dropped_piece_grid: Optional[DroppedPieceGrid] = None,
        score_keeper: Optional[Score] = None,
        render_mode: Optional[str] = None,
    ):
        super().__init__(
            screen,
            ((0, 0), (1, 0), (2, 0), (3, 0)),
            LIGHT_BLUE,
            top_left,
            dropped_piece_grid,
            (1, 0),
            score_keeper,
            render_mode,
        )


class TPiece(Piece):
    def __init__(
        self,
        screen: pygame.Surface,
        top_left: tuple,
        dropped_piece_grid: Optional[DroppedPieceGrid] = None,
        score_keeper: Optional[Score] = None,
        render_mode: Optional[str] = None,
    ):
        super().__init__(
            screen,
            ((0, 0), (1, 0), (1, 1), (2, 0)),
            PURPLE,
            top_left,
            dropped_piece_grid,
            (1, 0),
            score_keeper,
            render_mode,
        )
