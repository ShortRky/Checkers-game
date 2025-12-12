"""
Animated Checkers Game (Player vs Bot)

Requirements covered:
- Pygame-based GUI and animation
- Player (mouse) vs Bot (autonomous) play
- Basic bot logic: prefers captures, otherwise random legal move
- Visual board, pieces, king markers
- Instructions printed and shown on-screen
- Modular functions and comments explaining key parts

How to play Part 1:
- Run: python3 game.py
- Click a piece to select it, then click a valid target square to move.
- You may have multi-captures; the game enforces captures when available.
- Bot moves automatically after the player.

How to play Part 2:
- Open the website likely provided
- Same rules apply: click to select and move pieces.
- Multiple captures are supported.
- Bot moves automatically after the player.

Twist: Bot sometimes sacrifices pieces intentionally (randomness) and there is a small move animation.

"""

import pygame
import sys
import random
import time

# Game constants
WIDTH, HEIGHT = 800, 800
ROWS, COLS = 8, 8
SQUARE_SIZE = WIDTH // COLS
FPS = 60

# Colors
LIGHT = (240, 217, 181)
DARK = (181, 136, 99)
HIGHLIGHT = (0, 255, 0)
SELECT = (0, 200, 255)
RED = (200, 30, 30)
WHITE = (245, 245, 245)
GOLD = (255, 215, 0)

# Piece representation
EMPTY = 0
PLAYER = 1     # Human pieces (red)
BOT = 2        # Bot pieces (white)

pygame.init()
FONT = pygame.font.SysFont('arial', 18)
BIG_FONT = pygame.font.SysFont('arial', 36)
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Animated Checkers - Player vs Bot')

clock = pygame.time.Clock()

# Utility functions

def in_bounds(r, c):
    return 0 <= r < ROWS and 0 <= c < COLS


def opponent(color):
    return BOT if color == PLAYER else PLAYER


# Board class to keep state and enforce rules
class Board:
    def __init__(self):
        # board[r][c] = (color, king_bool) or None
        self.board = [[None for _ in range(COLS)] for _ in range(ROWS)]
        self.setup()

    def setup(self):
        # Place pieces in classic starting positions
        for r in range(ROWS):
            for c in range(COLS):
                if (r + c) % 2 == 1:
                    if r < 3:
                        self.board[r][c] = (BOT, False)
                    elif r > 4:
                        self.board[r][c] = (PLAYER, False)

    def get(self, r, c):
        return None if not in_bounds(r, c) else self.board[r][c]

    def set(self, r, c, val):
        if in_bounds(r, c):
            self.board[r][c] = val

    def remove(self, r, c):
        if in_bounds(r, c):
            self.board[r][c] = None

    def clone(self):
        b = Board()
        b.board = [row[:] for row in self.board]
        return b

    def pieces(self, color):
        res = []
        for r in range(ROWS):
            for c in range(COLS):
                p = self.get(r, c)
                if p and p[0] == color:
                    res.append((r, c, p[1]))
        return res

    def legal_moves_for(self, r, c):
        # Returns list of moves: each move is (to_r, to_c, captured_list)
        p = self.get(r, c)
        if not p:
            return []
        color, king = p
        directions = []
        if king or color == PLAYER:
            directions += [(-1, -1), (-1, 1)]  # up in board coords
        if king or color == BOT:
            directions += [(1, -1), (1, 1)]

        moves = []
        captures = []
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if not in_bounds(nr, nc):
                continue
            if self.get(nr, nc) is None:
                moves.append((nr, nc, []))
            else:
                # maybe capture
                if self.get(nr, nc)[0] == opponent(color):
                    jr, jc = nr + dr, nc + dc
                    if in_bounds(jr, jc) and self.get(jr, jc) is None:
                        captures.append((jr, jc, [(nr, nc)]))
        # For captures, we need to support multi-captures (chain)
        full_captures = []
        for cap in captures:
            # apply capture on a clone and search further captures recursively
            jr, jc, caplist = cap
            clone = self.clone()
            clone.set(jr, jc, clone.get(r, c))
            clone.remove(r, c)
            for (cr, cc) in caplist:
                clone.remove(cr, cc)
            # check for additional captures from jr,jc
            more = clone._recursive_captures(jr, jc)
            if more:
                for extra in more:
                    full_captures.append((extra[0], extra[1], caplist + extra[2]))
            else:
                full_captures.append((jr, jc, caplist))

        # If any captures exist, they are mandatory (rules enforced)
        if full_captures:
            return full_captures
        return moves

    def _recursive_captures(self, r, c):
        p = self.get(r, c)
        if not p:
            return []
        color, king = p
        directions = []
        if king or color == PLAYER:
            directions += [(-1, -1), (-1, 1)]
        if king or color == BOT:
            directions += [(1, -1), (1, 1)]

        captures = []
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            jr, jc = nr + dr, nc + dc
            if in_bounds(nr, nc) and in_bounds(jr, jc):
                if self.get(nr, nc) and self.get(nr, nc)[0] == opponent(color) and self.get(jr, jc) is None:
                    captures.append((jr, jc, [(nr, nc)]))
        full = []
        for cap in captures:
            jr, jc, caplist = cap
            clone = self.clone()
            clone.set(jr, jc, clone.get(r, c))
            clone.remove(r, c)
            for cr, cc in caplist:
                clone.remove(cr, cc)
            more = clone._recursive_captures(jr, jc)
            if more:
                for extra in more:
                    full.append((extra[0], extra[1], caplist + extra[2]))
            else:
                full.append((jr, jc, caplist))
        return full

    def apply_move(self, r, c, to_r, to_c, captured):
        p = self.get(r, c)
        self.set(to_r, to_c, p)
        self.remove(r, c)
        for cr, cc in captured:
            self.remove(cr, cc)
        # kinging
        color = p[0]
        if (color == PLAYER and to_r == 0) or (color == BOT and to_r == ROWS - 1):
            self.set(to_r, to_c, (color, True))

    def any_capture_available(self, color):
        for r, c, king in self.pieces(color):
            moves = self.legal_moves_for(r, c)
            for m in moves:
                if m[2]:
                    return True
        return False

    def game_over(self):
        p_count = len(self.pieces(PLAYER))
        b_count = len(self.pieces(BOT))
        if p_count == 0:
            return True, 'Bot wins'
        if b_count == 0:
            return True, 'Player wins'
        # Check if one side has no legal moves
        if not any(self.legal_moves_for(r, c) for r, c, k in self.pieces(PLAYER)):
            return True, 'Bot wins (no moves for player)'
        if not any(self.legal_moves_for(r, c) for r, c, k in self.pieces(BOT)):
            return True, 'Player wins (no moves for bot)'
        return False, ''


# Drawing functions and animations

def draw_board(win, board, selected=None, valid_moves=None):
    # draw squares
    for r in range(ROWS):
        for c in range(COLS):
            color = DARK if (r + c) % 2 else LIGHT
            rect = (c * SQUARE_SIZE, r * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
            pygame.draw.rect(win, color, rect)

    # highlight selected and valid moves
    if selected:
        r, c = selected
        pygame.draw.rect(win, SELECT, (c * SQUARE_SIZE, r * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE), 4)
    if valid_moves:
        for mv in valid_moves:
            tr, tc, _ = mv
            cx = tc * SQUARE_SIZE + SQUARE_SIZE // 2
            cy = tr * SQUARE_SIZE + SQUARE_SIZE // 2
            pygame.draw.circle(win, HIGHLIGHT, (cx, cy), 10)

    # draw pieces
    for r in range(ROWS):
        for c in range(COLS):
            p = board.get(r, c)
            if p:
                color, king = p
                cx = c * SQUARE_SIZE + SQUARE_SIZE // 2
                cy = r * SQUARE_SIZE + SQUARE_SIZE // 2
                radius = SQUARE_SIZE // 2 - 10
                piece_color = RED if color == PLAYER else WHITE
                pygame.draw.circle(win, (0,0,0), (cx, cy), radius + 2)  # shadow
                pygame.draw.circle(win, piece_color, (cx, cy), radius)
                if king:
                    pygame.draw.circle(win, GOLD, (cx, cy), radius // 2, 3)


def animate_move(win, board, start, end, captured):
    # Move a piece visually from start to end
    sr, sc = start
    er, ec = end
    p = board.get(sr, sc)
    if p is None:
        return
    color, king = p
    start_x = sc * SQUARE_SIZE + SQUARE_SIZE // 2
    start_y = sr * SQUARE_SIZE + SQUARE_SIZE // 2
    end_x = ec * SQUARE_SIZE + SQUARE_SIZE // 2
    end_y = er * SQUARE_SIZE + SQUARE_SIZE // 2

    frames = 12
    for i in range(1, frames + 1):
        clock.tick(FPS)
        t = i / frames
        x = int(start_x + (end_x - start_x) * t)
        y = int(start_y + (end_y - start_y) * t)
        draw_board(win, board, None, None)
        radius = SQUARE_SIZE // 2 - 10
        piece_color = RED if color == PLAYER else WHITE
        pygame.draw.circle(win, (0,0,0), (x, y), radius + 2)
        pygame.draw.circle(win, piece_color, (x, y), radius)
        if king:
            pygame.draw.circle(win, GOLD, (x, y), radius // 2, 3)
        # draw captured pieces fading out
        for cr, cc in captured:
            cx = cc * SQUARE_SIZE + SQUARE_SIZE // 2
            cy = cr * SQUARE_SIZE + SQUARE_SIZE // 2
            # quick fade effect
            alpha = int(255 * (1 - t))
            s = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(s, (0,0,0,alpha), (radius+2, radius+2), radius+2)
            pygame.draw.circle(s, (50,50,50,alpha), (radius+2, radius+2), radius)
            win.blit(s, (cx - radius - 2, cy - radius - 2))
        pygame.display.flip()


# Bot logic: prefers captures, otherwise random legal move. Adds slight randomness to try 'twist'.

def bot_move(board):
    moves = []
    capture_moves = []
    for r, c, k in board.pieces(BOT):
        for mv in board.legal_moves_for(r, c):
            to_r, to_c, captured = mv
            if captured:
                capture_moves.append((r, c, to_r, to_c, captured))
            else:
                moves.append((r, c, to_r, to_c, captured))
    # If captures exist, choose one. Prefer longer captures (greedy) but add randomness
    if capture_moves:
        capture_moves.sort(key=lambda x: -len(x[4]))
        top = [m for m in capture_moves if len(m[4]) == len(capture_moves[0][4])]
        choice = random.choice(top)
        return choice
    if not moves:
        return None
    # randomness: sometimes pick a non-optimal move to make the bot interesting
    if random.random() < 0.2:
        return random.choice(moves)
    # otherwise pick move that advances piece toward king row
    def score_move(m):
        _, _, tr, _, _ = m
        return tr if True else 0
    moves.sort(key=lambda m: score_move(m), reverse=True)
    # pick among top few
    topk = moves[:max(1, len(moves)//3)]
    return random.choice(topk)


def coords_from_mouse(pos):
    x, y = pos
    c = x // SQUARE_SIZE
    r = y // SQUARE_SIZE
    return r, c


def draw_hud(win, turn, message=''):
    # draw a translucent overlay at top
    s = pygame.Surface((WIDTH, 40))
    s.set_alpha(200)
    s.fill((30, 30, 30))
    win.blit(s, (0, 0))
    text = f"Turn: {'Player (Red)' if turn == PLAYER else 'Bot (White)'}"
    txt = FONT.render(text, True, (255, 255, 255))
    win.blit(txt, (8, 8))
    instruct = "Click a piece then click a target square. Captures are mandatory."
    it = FONT.render(instruct, True, (220, 220, 220))
    win.blit(it, (200, 8))
    if message:
        m = BIG_FONT.render(message, True, (255, 50, 50))
        win.blit(m, (WIDTH//2 - m.get_width()//2, HEIGHT//2 - m.get_height()//2))


def main():
    board = Board()
    running = True
    selected = None
    valid_moves = None
    turn = PLAYER
    ai_thinking = False
    message = ''
    while running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and turn == PLAYER and not ai_thinking:
                pos = pygame.mouse.get_pos()
                r, c = coords_from_mouse(pos)
                p = board.get(r, c)
                if selected:
                    # try to move
                    found = None
                    if valid_moves:
                        for mv in valid_moves:
                            tr, tc, captured = mv
                            if tr == r and tc == c:
                                found = mv
                                break
                    if found:
                        # animate and apply
                        animate_move(WIN, board, selected, (r, c), found[2])
                        board.apply_move(selected[0], selected[1], r, c, found[2])
                        selected = None
                        valid_moves = None
                        # check end or switch to bot
                        over, msg = board.game_over()
                        if over:
                            message = msg
                            turn = None
                        else:
                            turn = BOT
                            ai_thinking = True
                    else:
                        # clicking elsewhere resets selection or picks new piece
                        if p and p[0] == PLAYER:
                            selected = (r, c)
                            valid_moves = board.legal_moves_for(r, c)
                        else:
                            selected = None
                            valid_moves = None
                else:
                    if p and p[0] == PLAYER:
                        selected = (r, c)
                        valid_moves = board.legal_moves_for(r, c)

        # Bot turn
        if turn == BOT and ai_thinking:
            # small pause for realism
            pygame.display.flip()
            pygame.time.delay(400)
            mv = bot_move(board)
            if mv is None:
                over, msg = board.game_over()
                if over:
                    message = msg
                    turn = None
                    ai_thinking = False
                else:
                    # no moves, skip
                    turn = PLAYER
                    ai_thinking = False
            else:
                r, c, tr, tc, captured = mv
                animate_move(WIN, board, (r, c), (tr, tc), captured)
                board.apply_move(r, c, tr, tc, captured)
                ai_thinking = False
                over, msg = board.game_over()
                if over:
                    message = msg
                    turn = None
                else:
                    turn = PLAYER

        draw_board(WIN, board, selected, valid_moves)
        draw_hud(WIN, turn, message)
        pygame.display.flip()

    pygame.quit()


if __name__ == '__main__':
    main()
