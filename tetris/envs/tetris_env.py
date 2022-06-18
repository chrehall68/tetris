import gym
from typing import Optional
from tetris.envs.game.game import *
from gym import spaces
import pygame
import numpy


PIECE_TO_NUMBER = {
    None: 0,
    OPiece: 1,
    SPiece: 2,
    ZPiece: 3,
    LPiece: 4,
    JPiece: 5,
    IPiece: 6,
    TPiece: 7,
}
ACTION_MAPPINGS = {
    0: pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_UP}),
    1: pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_DOWN}),
    2: pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_LEFT}),
    3: pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RIGHT}),
    4: pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_z}),
    5: pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_c}),
    6: pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_SPACE}),
    7: pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_q}),  # don't do anything
}


class TetrisEnv(gym.Env):
    metadata = {"render_modes": ["human"]}

    def __init__(self, render_mode: Optional[str] = None) -> None:
        self.render_mode = render_mode

        self.action_space = spaces.Discrete(len(KEY_MAPPINGS))

        self.observation_space = spaces.Dict(
            {
                "next_pieces": spaces.Box(1, 7, (3,), dtype=numpy.int64),
                "held_piece": spaces.Box(0, 7, (1,), dtype=numpy.int64),
                "dropped_piece_grid": spaces.Box(
                    0,
                    1,
                    (PLAYER_GRID_DIMENSIONS[1] * PLAYER_GRID_DIMENSIONS[0],),
                    dtype=numpy.int64,
                ),
                "cur_piece_locat": spaces.Box(
                    0,
                    max(PLAYER_GRID_DIMENSIONS),
                    (8,),
                    dtype=numpy.int64,
                ),
            }
        )
        self.game = TetrisGame(render_mode=self.render_mode)
        self.past_score = 0

    def reset(self, seed=None, return_info=False, options=None):
        self.past_score = 0
        self.game.reset()

        if return_info:
            return self._get_obs(), self._get_info()
        return self._get_obs()

    def render(self):
        assert self.render_mode == "human"
        self.game.render()

    def step(self, action):
        # print("action is", action, "and type is", type(action))
        try:
            self.game.step([ACTION_MAPPINGS[action]])
        except Exception:
            self.game.step([ACTION_MAPPINGS[action.item()]])  # happens for dqn
        return self._get_obs(), self._get_reward(), self._get_done(), self._get_info()

    def _get_obs(self):
        for T, val in PIECE_TO_NUMBER.items():
            if (
                self.game.holder.held_piece == T
                or type(self.game.holder.held_piece) == T
            ):
                held_piece_val = val
                break

        next_pieces_val = []
        for piece in self.game.next_pieces.next_pieces:
            for T, val in PIECE_TO_NUMBER.items():
                if piece == T:
                    next_pieces_val.append(val)
                    break
        next_pieces_val = tuple(next_pieces_val)

        cur_piece_locat = []
        for block in self.game.cur_piece.blocks:
            temp = block.top_left // SPACE_SIZE
            cur_piece_locat.append((temp.x, temp.y))
        cur_piece_locat = tuple(cur_piece_locat)

        return {
            "next_pieces": numpy.array(next_pieces_val, dtype=numpy.int64),
            "held_piece": numpy.array([held_piece_val], dtype=numpy.int64),
            "dropped_piece_grid": numpy.array(
                self.game.dropped_piece_grid.numeric_used_spaces, dtype=numpy.int64
            ).flatten(),
            "cur_piece_locat": numpy.array(
                cur_piece_locat, dtype=numpy.int64
            ).flatten(),
        }

    def _get_reward(self):
        """
        Idea:
        There are 3 basic states:

        * height decreases (vv good)
        * height stays the same (debatable)
        * height increases (bad)

        If height decreases, simple positive reward

        If height stays the same, then it depends on how close each of the
        blocks is to the bottom of the screen (ie how deep in it went)

        If height increases and no lines were cleared, just negative. If it
        increases and lines were cleared, then adjust the negative (by how
        much remains TBD)
        """

        def sinusoidal_amplify(r):
            return numpy.sin(r * numpy.pi / 2)

        # reward based on height
        if self.game.just_dropped:
            delta_h = (
                self.game.dropped_piece_grid.height
                - self.game.dropped_piece_grid.past_height
            )
            if abs(delta_h) > 4:
                print("past height", self.game.dropped_piece_grid.past_height)
                print("cur height", self.game.dropped_piece_grid.height)
                print(
                    "cur grid",
                    numpy.array(self.game.dropped_piece_grid.numeric_used_spaces),
                )
                raise Exception("FAILED")

            # case 1 - height decreases
            if delta_h < 0:
                return (
                    sinusoidal_amplify(
                        sinusoidal_amplify(
                            sinusoidal_amplify(-delta_h / LINE_CLEAR_WEIGHT)
                        )
                    )
                    * SCORE_DIVISION["line_clear"]
                )

            # case 2 or 3 (delta_h >= 0)
            ret = (
                self.game.dropped_piece_grid.last_piece_ending_height
                / 20
                * SCORE_DIVISION["ending_height"]
            )
            return ret - sinusoidal_amplify(delta_h / 4) * SCORE_DIVISION["line_add"]

        # discourage ending the game
        if not self.game.run:
            return -1

        return 0

    def _get_done(self):
        return not self.game.run

    def _get_info(self):
        return {}

    def close(self):
        self.game.run = False
        pygame.quit()
