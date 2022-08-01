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
    metadata = {
        "render_modes": ["human"],
        "reward_modes": ["sparse", "distance", "solid", "sparsev2"],
        "step_modes": ["positive", "negative", "none"],
    }

    def __init__(
        self,
        render_mode: Optional[str] = None,
        reward_mode: Optional[str] = None,
        step_mode: Optional[str] = None,
        max_timesteps: Optional[int] = 500,
        penalize_illegal: Optional[bool] = True,
    ) -> None:
        self.render_mode = render_mode

        self.action_space = spaces.Discrete(len(KEY_MAPPINGS))

        self.observation_space = spaces.Dict(
            {
                "held_piece": spaces.Box(0, 7, (1,), dtype=numpy.int64),
                "dropped_piece_grid": spaces.Box(
                    0,
                    2,
                    (PLAYER_GRID_DIMENSIONS[1] * PLAYER_GRID_DIMENSIONS[0],),
                    dtype=numpy.int64,
                ),
            }
        )
        self.game = TetrisGame(render_mode=self.render_mode)
        self.past_score = 0

        self.reward_functions = {
            "sparse": self._sparse_reward,
            "distance": self._distance_based_reward,
            "solid": self._solid_reward,
            "sparsev2": self._sparse_reward_v2,
        }
        self.step_function = {
            "positive": lambda: 0.001,
            "negative": lambda: -0.001,
            "none": lambda: 0,
        }

        if (
            reward_mode is not None
            and reward_mode in TetrisEnv.metadata["reward_modes"]
        ):
            self.reward_mode = reward_mode
        else:
            self.reward_mode = "sparse"  # sparse is default
        if step_mode is not None and step_mode in TetrisEnv.metadata["step_modes"]:
            self.step_mode = step_mode
        else:
            self.step_mode = "positive"  # positive step by default

        self.penalize_illegal = penalize_illegal
        self.penalties = {False: lambda: 0, True: self._penalize_illegal_moves}

        print(f"using reward mode {self.reward_mode}")
        print(f"using step mode {self.step_mode}")
        print(f"{'' if self.penalize_illegal else 'not '}penalizing illegal moves")

        self.cur_timesteps = 0
        self.max_timesteps = max_timesteps

    def reset(self, seed=None, return_info=False, options=None):
        self.past_score = 0
        self.cur_timesteps = 0
        self.game.reset()

        if return_info:
            return self._get_obs(), self._get_info()
        return self._get_obs()

    def render(self, render_mode=None):
        if render_mode is None:
            render_mode = self.render_mode
        else:
            self.render_mode = render_mode

        assert self.render_mode == "human"
        self.game.render()

    def step(self, action):
        try:
            self.game.step([ACTION_MAPPINGS[action]])
        except Exception:
            self.game.step([ACTION_MAPPINGS[action.item()]])  # happens for dqn
        self.cur_timesteps += 1
        if self.cur_timesteps >= self.max_timesteps:
            self.game.run = False
        return self._get_obs(), self._get_reward(), self._get_done(), self._get_info()

    def reward(self):
        return self._get_reward()

    def _get_obs(self):
        for T, val in PIECE_TO_NUMBER.items():
            if (
                self.game.holder.held_piece == T
                or type(self.game.holder.held_piece) == T
            ):
                held_piece_val = val
                break

        dropped_piece_grid = list(self.game.dropped_piece_grid.numeric_used_spaces)
        for y in range(len(dropped_piece_grid)):
            dropped_piece_grid[y] = list(dropped_piece_grid[y])
        for block in self.game.cur_piece.blocks:
            temp = block.top_left // SPACE_SIZE
            dropped_piece_grid[temp.y][temp.x] = 2
        for y in range(len(dropped_piece_grid)):
            dropped_piece_grid[y] = tuple(dropped_piece_grid[y])

        return {
            "held_piece": numpy.array([held_piece_val], dtype=numpy.int64),
            "dropped_piece_grid": numpy.array(
                tuple(dropped_piece_grid), dtype=numpy.int64
            ).flatten(),
        }

    def _get_reward(self):
        return (
            self.reward_functions[self.reward_mode]()
            + self.step_function[self.step_mode]()
            + self.penalties[self.penalize_illegal]()
        )

    def _penalize_illegal_moves(self) -> float:
        if not self.game.valid_last_move:
            return -10
        return 0

    def _solid_reward(self) -> float:
        """
        Idea: give score based on how far down it made and how
        many empty spaces are underneath it when placed
        """
        # get current height
        max_depth = 0
        for block in self.game.cur_piece.blocks:
            max_depth = max(max_depth, block.top_left.y // SPACE_SIZE)
        down_score = self._sinusoidal_amplify(max_depth / 19) * 1  # 0.01 is max

        solid_score = 0
        if self.game.just_dropped:
            spaces_beneath = self.game.dropped_piece_grid.empty_spaces_beneath
            if spaces_beneath == 0:
                solid_score = 5
            else:
                solid_score = 5 - 4 * (self._sigmoid(spaces_beneath) * 2 - 1)

        return down_score + solid_score + self._sparse_reward() * 100

    def _sparse_reward(self) -> float:
        """
        Idea: give score only based on clearing lines
        """
        return self._sinusoidal_amplify(
            LINE_CLEAR_SCORES[self.game.dropped_piece_grid.lines_just_cleared] / 800
        )

    def _sparse_reward_v2(self) -> float:
        return self._sparse_reward() * 100

    def _sinusoidal_amplify(self, inp) -> float:
        return numpy.sin(numpy.pi * 0.5 * inp)

    def _sigmoid(self, inp) -> float:
        return 1 / (1 + numpy.exp(-inp))

    def _distance_based_reward(self) -> float:
        """
        Idea: make reward based on distance from "ideal" state
        """

        def distance(piece: Piece):
            ideal_ul, ideal_arrangement = piece.get_best_position()

            dist = sqrt(
                (ideal_ul.x - piece.top_left.x) ** 2
                + (ideal_ul.y - piece.top_left.y) ** 2
            )

            ret = (1 / (dist + 1)) * 0.005
            if ideal_arrangement == piece.arrangement:
                ret += 0.005
            if ideal_ul == piece.top_left and ideal_arrangement == piece.arrangement:
                ret += 0.01
            return ret

        ret = distance(self.game.cur_piece)
        # huge reward for getting this
        if self.game.just_dropped:
            ret += self._sinusoidal_amplify(
                LINE_CLEAR_SCORES[self.game.dropped_piece_grid.lines_just_cleared] / 800
            )
        return ret

    def _get_done(self):
        return not self.game.run

    def _get_info(self):
        return {}

    def close(self):
        self.game.run = False
        pygame.quit()
