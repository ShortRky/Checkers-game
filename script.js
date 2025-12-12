// Full web Checkers implementation

const canvas = document.getElementById('board');
const ctx = canvas.getContext('2d');
const WIDTH = canvas.width;
const HEIGHT = canvas.height;
const ROWS = 8;
const COLS = 8;
const SQUARE = WIDTH / COLS;

const LIGHT = '#F0D9B5';
const DARK = '#B58863';
const SELECT = '#00C8FF';
const HIGHLIGHT = '#00FF00';
const RED = '#C81E1E';
const WHITE = '#F5F5F5';
const GOLD = '#FFD700';

const PLAYER = 1; // red
const BOT = 2;    // white

let board = [];
let selected = null;
let validMoves = [];
let turn = PLAYER;
let animating = false;
let showCoords = false;
let status = document.getElementById('status');

function newGame() {
  board = [];
  for (let r = 0; r < ROWS; r++) {
    board[r] = [];
    for (let c = 0; c < COLS; c++) {
      if ((r + c) % 2 === 1) {
        if (r < 3) board[r][c] = {color: BOT, king: false};
        else if (r > 4) board[r][c] = {color: PLAYER, king: false};
        else board[r][c] = null;
      } else {
        board[r][c] = null;
      }
    }
  }
  selected = null;
  validMoves = [];
  turn = PLAYER;
  animating = false;
  status.textContent = '';
  draw();
}

function inBounds(r, c) { return r >= 0 && r < ROWS && c >= 0 && c < COLS; }
function opponent(color) { return color === PLAYER ? BOT : PLAYER; }

function pieceAt(r, c) { return inBounds(r, c) ? board[r][c] : null; }

function legalMovesFor(r, c) {
  const p = pieceAt(r, c);
  if (!p) return [];
  const color = p.color;
  const king = p.king;
  const dirs = [];
  if (king || color === PLAYER) dirs.push([-1, -1], [-1, 1]);
  if (king || color === BOT) dirs.push([1, -1], [1, 1]);

  const moves = [];
  const caps = [];
  for (const [dr, dc] of dirs) {
    const nr = r + dr, nc = c + dc;
    if (!inBounds(nr, nc)) continue;
    if (pieceAt(nr, nc) === null) moves.push({tr: nr, tc: nc, cap: []});
    else if (pieceAt(nr, nc).color === opponent(color)) {
      const jr = nr + dr, jc = nc + dc;
      if (inBounds(jr, jc) && pieceAt(jr, jc) === null) caps.push({tr: jr, tc: jc, cap: [[nr, nc]]});
    }
  }

  // recursive chaining for captures
  const fullCaps = [];
  for (const cap of caps) {
    const clone = cloneBoard();
    clone[cap.tr][cap.tc] = clone[r][c];
    clone[r][c] = null;
    for (const [cr, cc] of cap.cap) clone[cr][cc] = null;
    const more = recursiveCaptures(clone, cap.tr, cap.tc);
    if (more.length) {
      for (const m of more) fullCaps.push({tr: m.tr, tc: m.tc, cap: cap.cap.concat(m.cap)});
    } else {
      fullCaps.push(cap);
    }
  }

  if (fullCaps.length) return fullCaps;
  return moves;
}

function recursiveCaptures(bd, r, c) {
  const p = bd[r][c];
  if (!p) return [];
  const color = p.color;
  const king = p.king;
  const dirs = [];
  if (king || color === PLAYER) dirs.push([-1, -1], [-1, 1]);
  if (king || color === BOT) dirs.push([1, -1], [1, 1]);
  const caps = [];
  for (const [dr, dc] of dirs) {
    const nr = r + dr, nc = c + dc;
    const jr = nr + dr, jc = nc + dc;
    if (inBounds(nr, nc) && inBounds(jr, jc)) {
      if (bd[nr][nc] && bd[nr][nc].color === opponent(color) && bd[jr][jc] === null) caps.push({tr: jr, tc: jc, cap: [[nr, nc]]});
    }
  }
  const full = [];
  for (const cap of caps) {
    const clone = cloneBoard(bd);
    clone[cap.tr][cap.tc] = clone[r][c];
    clone[r][c] = null;
    for (const [cr, cc] of cap.cap) clone[cr][cc] = null;
    const more = recursiveCaptures(clone, cap.tr, cap.tc);
    if (more.length) {
      for (const m of more) full.push({tr: m.tr, tc: m.tc, cap: cap.cap.concat(m.cap)});
    } else full.push(cap);
  }
  return full;
}

function cloneBoard(src) {
  const b = [];
  const s = src || board;
  for (let r = 0; r < ROWS; r++) {
    b[r] = [];
    for (let c = 0; c < COLS; c++) {
      const p = s[r][c];
      b[r][c] = p ? {color: p.color, king: p.king} : null;
    }
  }
  return b;
}

function anyCaptureAvailable(color) {
  for (let r = 0; r < ROWS; r++) for (let c = 0; c < COLS; c++) {
    const p = pieceAt(r, c);
    if (p && p.color === color) {
      const moves = legalMovesFor(r, c);
      if (moves.some(m => m.cap && m.cap.length)) return true;
    }
  }
  return false;
}

function gameOver() {
  const pc = countPieces(PLAYER);
  const bc = countPieces(BOT);
  if (!pc) return {over: true, msg: 'Bot wins'};
  if (!bc) return {over: true, msg: 'Player wins'};
  if (!hasAnyMoves(PLAYER)) return {over: true, msg: 'Bot wins (player has no moves)'};
  if (!hasAnyMoves(BOT)) return {over: true, msg: 'Player wins (bot has no moves)'};
  return {over: false, msg: ''};
}

function countPieces(color) {
  let cnt = 0;
  for (let r = 0; r < ROWS; r++) for (let c = 0; c < COLS; c++) if (pieceAt(r,c) && pieceAt(r,c).color === color) cnt++;
  return cnt;
}
function hasAnyMoves(color) {
  for (let r = 0; r < ROWS; r++) for (let c = 0; c < COLS; c++) {
    const p = pieceAt(r, c);
    if (p && p.color === color) {
      if (legalMovesFor(r, c).length) return true;
    }
  }
  return false;
}

function applyMove(r, c, tr, tc, cap) {
  const p = pieceAt(r, c);
  board[tr][tc] = p;
  board[r][c] = null;
  for (const [cr, cc] of cap) board[cr][cc] = null;
  // kinging
  if (p.color === PLAYER && tr === 0) board[tr][tc].king = true;
  if (p.color === BOT && tr === ROWS-1) board[tr][tc].king = true;
}

function trySelect(r, c) {
  const p = pieceAt(r, c);
  if (p && p.color === PLAYER) {
    selected = [r, c];
    validMoves = legalMovesFor(r, c);
  } else {
    selected = null;
    validMoves = [];
  }
}

function coordsFromMouse(e) {
  const rect = canvas.getBoundingClientRect();
  const x = e.clientX - rect.left;
  const y = e.clientY - rect.top;
  const c = Math.floor(x / SQUARE);
  const r = Math.floor(y / SQUARE);
  return [r, c];
}

canvas.addEventListener('click', (e) => {
  if (animating || turn !== PLAYER) return;
  const [r, c] = coordsFromMouse(e);
  const p = pieceAt(r, c);
  if (selected) {
    // look for matching move
    let found = null;
    for (const mv of validMoves) if (mv.tr === r && mv.tc === c) { found = mv; break; }
    if (found) {
      animateMove(selected, [r, c], found.cap, () => {
        applyMove(selected[0], selected[1], r, c, found.cap);
        selected = null; validMoves = [];
        const end = gameOver();
        if (end.over) { status.textContent = end.msg; turn = null; return; }
        turn = BOT; window.setTimeout(botTurn, 300);
      });
    } else {
      if (p && p.color === PLAYER) trySelect(r, c);
      else { selected = null; validMoves = []; draw(); }
    }
  } else {
    if (p && p.color === PLAYER) trySelect(r, c);
  }
  draw();
});

function botTurn() {
  if (turn !== BOT) return;
  const moves = [];
  const caps = [];
  for (let r = 0; r < ROWS; r++) for (let c = 0; c < COLS; c++) {
    const p = pieceAt(r, c);
    if (p && p.color === BOT) {
      const mvs = legalMovesFor(r, c);
      for (const mv of mvs) {
        if (mv.cap && mv.cap.length) caps.push([r,c,mv]); else moves.push([r,c,mv]);
      }
    }
  }
  let choice = null;
  if (caps.length) {
    caps.sort((a,b)=> b[2].cap.length - a[2].cap.length);
    const top = caps.filter(x => x[2].cap.length === caps[0][2].cap.length);
    choice = top[Math.floor(Math.random()*top.length)];
  } else if (moves.length) {
    if (Math.random() < 0.2) choice = moves[Math.floor(Math.random()*moves.length)];
    else {
      moves.sort((a,b)=> b[2].tr - a[2].tr);
      const topk = moves.slice(0, Math.max(1, Math.floor(moves.length/3)));
      choice = topk[Math.floor(Math.random()*topk.length)];
    }
  }
  if (!choice) {
    const end = gameOver();
    if (end.over) { status.textContent = end.msg; turn = null; }
    else turn = PLAYER;
    draw();
    return;
  }
  const [r, c, mv] = choice;
  animateMove([r,c], [mv.tr, mv.tc], mv.cap, () => {
    applyMove(r,c,mv.tr,mv.tc,mv.cap);
    const end = gameOver();
    if (end.over) { status.textContent = end.msg; turn = null; draw(); return; }
    turn = PLAYER; draw();
  });
}

function animateMove(start, end, cap, onDone) {
  animating = true;
  const sr = start[0], sc = start[1];
  const er = end[0], ec = end[1];
  const sx = sc * SQUARE + SQUARE/2; const sy = sr * SQUARE + SQUARE/2;
  const ex = ec * SQUARE + SQUARE/2; const ey = er * SQUARE + SQUARE/2;
  const frames = 12;
  let i = 0;
  function frame() {
    i++;
    const t = i/frames;
    draw();
    const x = sx + (ex - sx) * t;
    const y = sy + (ey - sy) * t;
    const p = pieceAt(sr, sc);
    if (p) {
      drawPieceAtXY(x, y, p.color, p.king);
    }
    // fade captured pieces
    for (const [cr, cc] of cap) {
      const cx = cc * SQUARE + SQUARE/2; const cy = cr * SQUARE + SQUARE/2;
      ctx.globalAlpha = 1 - t; drawPieceAtXY(cx, cy, opponent(turn), false); ctx.globalAlpha = 1;
    }
    if (i < frames) requestAnimationFrame(frame);
    else { animating = false; onDone(); }
  }
  requestAnimationFrame(frame);
}

function drawPieceAtXY(x, y, color, king) {
  const radius = SQUARE/2 - 10;
  ctx.beginPath(); ctx.fillStyle = '#000'; ctx.arc(x, y, radius+2, 0, Math.PI*2); ctx.fill();
  ctx.beginPath(); ctx.fillStyle = (color === PLAYER) ? RED : WHITE; ctx.arc(x, y, radius, 0, Math.PI*2); ctx.fill();
  if (king) { ctx.lineWidth = 3; ctx.strokeStyle = GOLD; ctx.beginPath(); ctx.arc(x, y, radius/2, 0, Math.PI*2); ctx.stroke(); }
}

function draw() {
  // board
  for (let r = 0; r < ROWS; r++) for (let c = 0; c < COLS; c++) {
    const color = (r+c)%2 ? DARK : LIGHT;
    ctx.fillStyle = color;
    ctx.fillRect(c*SQUARE, r*SQUARE, SQUARE, SQUARE);
  }
  // coords
  if (showCoords) {
    ctx.fillStyle = 'rgba(0,0,0,0.3)'; ctx.font = '12px Arial';
    for (let r=0;r<ROWS;r++) for (let c=0;c<COLS;c++) ctx.fillText(`${r},${c}`, c*SQUARE+6, r*SQUARE+14);
  }
  // highlights
  if (selected) {
    ctx.strokeStyle = SELECT; ctx.lineWidth = 4;
    ctx.strokeRect(selected[1]*SQUARE+2, selected[0]*SQUARE+2, SQUARE-4, SQUARE-4);
  }
  for (const mv of validMoves) {
    ctx.fillStyle = HIGHLIGHT; ctx.beginPath(); ctx.arc(mv.tc*SQUARE+SQUARE/2, mv.tr*SQUARE+SQUARE/2, 8, 0, Math.PI*2); ctx.fill();
  }
  // pieces
  for (let r = 0; r < ROWS; r++) for (let c = 0; c < COLS; c++) {
    const p = pieceAt(r,c);
    if (p) drawPieceAtXY(c*SQUARE+SQUARE/2, r*SQUARE+SQUARE/2, p.color, p.king);
  }
}

// Controls
newGame();

document.getElementById('newGame').addEventListener('click', () => newGame());
document.getElementById('showCoords').addEventListener('change', (e) => { showCoords = e.target.checked; draw(); });

// initial draw
draw();