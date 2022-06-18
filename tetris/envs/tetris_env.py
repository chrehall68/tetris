from math import sqrt
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
        Idea: make reward based on distance from "ideal" state
        """

        def distance(piece: Piece):
            ideal_ul, ideal_arrangement = piece.get_best_position()

            dist = sqrt(
                (ideal_ul.x - piece.top_left.x) ** 2
                + (ideal_ul.y - piece.top_left.y) ** 2
            )
            ret = dist / 4000  # should give numbers <= 0.1
            if ideal_arrangement == piece.arrangement:
                ret += 0.1
            return ret

        ret = distance(self.game.cur_piece)
        if self.game.just_dropped:
            ret += 0.7 * self.game.dropped_piece_grid.lines_just_cleared
        return ret

    def _get_done(self):
        return not self.game.run

    def _get_info(self):
        return {}

    def close(self):
        self.game.run = False
        pygame.quit()
