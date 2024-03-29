from copy import copy, deepcopy
import pygame
from tetris.envs.game.constants import *
from tetris.envs.game.dropped_piece_grid import DroppedPieceGrid
from tetris.envs.game.line_grid import LineGrid
from tetris.envs.game.piece import *
from tetris.envs.game.score import Score
from tetris.envs.game.next_pieces import NextPieces
from tetris.envs.game.holder import Holder


class TetrisGame:
    def __init__(self, render_mode: Optional[str] = None):
        self.render_mode = render_mode
        self.reset()

    def instantiate_piece(self, uninstantiated_piece) -> Piece:
        return uninstantiated_piece(
            self.player_screen,
            BLOCK_START,
            self.dropped_piece_grid,
            self.score_keeper,
            self.render_mode,
        )

    def get_next_piece(self):
        self.dropped_piece_grid += self.cur_piece
        self.cur_piece = self.instantiate_piece(self.next_pieces.step())
        if self.dropped_piece_grid.contains_piece(self.cur_piece):
            self.run = False
        self.holdable = True
        self.just_dropped = True

    def hold_piece(self, events):
        for event in events:
            if (
                event.type == pygame.KEYDOWN
                and event.key in KEY_MAPPINGS
                and KEY_MAPPINGS[event.key] == "hold"
            ):
                if self.holdable:
                    self.cur_piece = self.holder.swap(self.cur_piece)
                    if self.cur_piece is None:
                        self.get_next_piece()
                    self.holdable = False
                else:
                    self.valid_last_move = False

    def reset(self):
        """
        Resets tetris.
        """
        if self.render_mode == "human" or self.render_mode == "rgb-array":
            pygame.init()
            self.screen = pygame.display.set_mode(FULL_WINDOW_SIZE)
            pygame.display.set_caption("tetris")
            try:
                pygame.display.set_icon(pygame.image.load("tetris/envs/game/logo.png"))
            except Exception:
                pass

        # screens to draw on
        self.player_screen = pygame.Surface(PLAYER_DIMENSIONS)
        self.score_screen = pygame.Surface(SCORE_DIMENSIONS)
        self.next_screen = pygame.Surface(NEXT_PIECES_DIMENSIONS)
        self.holder_screen = pygame.Surface(HOLDER_DIMENSIONS)

        self.run = True

        # useful data variables
        self.holdable = True
        self.executions = 0
        self.just_dropped = False
        self.max_delta_h = 0  # max delta_h of cur piece. It is in spaces, not pixels
        self.valid_last_move = True

        # variables used to run the game
        self.score_keeper = Score(self.score_screen, self.render_mode)
        self.dropped_piece_grid = DroppedPieceGrid(self.score_keeper, self.render_mode)
        self.line_grid = LineGrid(self.player_screen, render_mode=self.render_mode)
        self.next_pieces = NextPieces(self.next_screen, self.render_mode)
        self.holder = Holder(self.holder_screen, self.render_mode)
        self.cur_piece = self.instantiate_piece(self.next_pieces.step())

    def render(self):
        assert self.render_mode == "human" or self.render_mode == "rgb-array"
        self.screen.fill(BG_COLOR)
        self.player_screen.fill(BG_COLOR)

        # player draws
        self.cur_piece.draw()
        self.line_grid.draw()
        self.dropped_piece_grid.draw()

        # score draws
        self.score_keeper.draw()

        # next pieces draws
        self.next_pieces.draw()

        # holder draws
        self.holder.draw()

        # draw the individual screens
        self.screen.blit(self.score_screen, SCORE_SCREEN_POS)
        self.screen.blit(self.player_screen, PLAYER_SCREEN_POS)
        self.screen.blit(self.next_screen, NEXT_PIECES_SCREEN_POS)
        self.screen.blit(self.holder_screen, HOLDER_SCREEN_POS)

        pygame.display.update()
        if self.render_mode == "rgb-array":
            return pygame.surfarray.array3d(self.screen)

    def step(self, events: Optional[pygame.event.Event] = None):
        if events is None:
            actual_events = pygame.event.get()

            # if there's a quit
            for event in actual_events:
                if event.type == pygame.QUIT:
                    self.run = False
        else:
            actual_events = events

        self.valid_last_move = True
        self.just_dropped = False
        self.hold_piece(actual_events)
        self.valid_last_move = (
            self.cur_piece.move(actual_events) and self.valid_last_move
        )
        self.executions += 1

        if self.cur_piece.out:
            self.get_next_piece()
            self.executions = STEPS_BETWEEN_DOWNS // 2

        if self.run and self.executions == STEPS_BETWEEN_DOWNS:
            self.executions = 0
            if not self.cur_piece.move_down():
                self.get_next_piece()
                self.executions = STEPS_BETWEEN_DOWNS // 2

        if not self.valid_last_move:
            print("invalid move")

    def is_move_valid(self, event):
        if event.type != pygame.KEYDOWN:
            return False

        # hold a piece
        if event.key == pygame.K_c:
            return self.holdable

        # do nothing
        elif event.key == pygame.K_q:
            return True

        # move/rotate
        else:
            clone = self.cur_piece.clone()
            return clone.move([event])

    def play_execution_based(self):
        self.step()
        self.render()
        pygame.time.wait(50)

    @property
    def total_lines_cleared(self):
        return self.dropped_piece_grid.total_lines_cleared


"""
gamer = TetrisGame(render_mode="human")
while gamer.run:
    gamer.play_execution_based()
    if gamer.executions % 20 == 0:
        (
            gamer.cur_piece.top_left,
            gamer.cur_piece.arrangement,
        ) = gamer.cur_piece.get_best_position()
        gamer.cur_piece._get_blocks()
"""
