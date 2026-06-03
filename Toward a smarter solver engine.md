# Toward a smarter solver engine

## Example choices

```bash
# In branch Game-002-vs-Jeanne - the commit after d7228313c6ed930ae052a18cdd8da11844da3016
$ date; python ./qwirkle_solver.py; date
Thu May 28 03:52:26 EDT 2026
Total legal multi-tile moves: 81
Rank 1: 6 points -> ,(-9, -4): Tile(color='yellow', shape='crossx'), (-8, -4): Tile(color='yellow', shape='clover'), (-7, -4): Tile(color='yellow', shape='circle')
Rank 2: 6 points -> ,(-9, -4): Tile(color='yellow', shape='clover'), (-8, -4): Tile(color='yellow', shape='crossx'), (-7, -4): Tile(color='yellow', shape='circle')
Rank 3: 6 points -> ,(8, 4): Tile(color='yellow', shape='clover'), (9, 4): Tile(color='yellow', shape='circle'), (10, 4): Tile(color='yellow', shape='crossx')
Rank 4: 6 points -> ,(8, 4): Tile(color='yellow', shape='clover'), (9, 4): Tile(color='yellow', shape='crossx'), (10, 4): Tile(color='yellow', shape='circle')
Thu May 28 03:52:28 EDT 2026

## 6/3/2026 - Claude Opus 4.8 MAX effort - Did a good job: See a3b72c7eef14105f0a7d44d85c42d2cab63f0db3
Paste from chat:

The answer: you're checkmated by 3 points — but it's close enough to steal if Jeanne slips
Her Blue trio resolved the hidden information. The bag is now empty and her hand is fully known, so I solved the rest exactly (minimax, both sides optimal, including the +6 go-out bonus). Three independent methods all agree: best play → Jeanne 190, You 187.

State now: Jeanne 177, You 157, your move. Her hand: red star · orange diamond · orange square · orange crossx ×2.

The forced line:

# Side Pts Play
1 You 9 green crossx (2,−7) + yellow crossx (2,−6)
2 Jeanne 8 orange trio at (−7,2)(−6,2)(−5,2) — caps the x=−5 square column to 5
3 You 9 blue/orange/purple star at (−2,6)(−1,6)(0,6)
4 Jeanne 5 red star at (−2,5)
5 You 6 +6 go-out yellow diamond (4,−6) — empties your hand, ends the game, denies her last orange crossx
You net +30, she nets +13, and from a 20-point hole that lands at −3.

Why it can't be forced to a win:

Her orange-trio 8 is unblockable — (−5,2) accepts only a square (you hold none), and (−6,2)/(−7,2) are isolated until she plays them.
You can't go out in 2 turns — your yellow crossx · green crossx · yellow diamond share neither a color nor a shape, so they can't be one line. That forces a 3rd turn, which is exactly why you can't go out before her red star.
I checked the obvious swindle (sacrificing points to block her red star at (−2,5)): it loses more than it denies. Not worth it.
Your real shot: it's only 3 points, and her two scoring plays are both non-obvious. The orange trio in particular — stacking the far-left square column to 5 — is easy to miss. Play the line above and make her find every point. If she plays her orange tiles for 6 instead of 8, or misses the red-star spot, you win outright.

Recommended move right now: green crossx (2,−7) + yellow crossx (2,−6), for 9. It's in every optimal line, sits in its own corner of the board, and gives Jeanne nothing.

Want me to map out the best responses if Jeanne deviates from the orange trio (so you know instantly whether her actual move hands you the win), or is the recommendation enough to play on?

In the 4th move you show - Jeanne red star at (−2,5).  That's only 3 points, right?
Excellent catch — let me check that precisely, because it touches the exact pivot of this endgame. You're right to question it.

Bash Verify red star value and the reorder/no-feed line
IN
cd c:/src/fun/qwirkle-solver && .venv/Scripts/python.exe -c "
import json
from collections import Counter
from qwirkle_core import Tile,QwirkleEngine,generate_all_multi_moves
d=json.load(open('game_state.json'))
board={}
for m in d['moves']:
    for t in m['tiles']:
        board[(t['x'],t['y'])]=Tile(t['color'],t['shape'])
def ap(b,pl):
    nb=dict(b)
    for (x,y),t in pl: nb[(x,y)]=t
    return nb
def s1(b,x,y,t):
    e=QwirkleEngine(); e.load_board_state(b)
    return e.calculate_score((x,y),t) if e.is_legal_move((x,y),t) else None
GC=Tile('green','crossx');YC=Tile('yellow','crossx');YD=Tile('yellow','diamond')
OS=Tile('orange','star');BS=Tile('blue','star');PS=Tile('purple','star')
RS=Tile('red','star');OC=Tile('orange','crossx');OD=Tile('orange','diamond');OQ=Tile('orange','square')
move1=[((2,-7),GC),((2,-6),YC)]
move2=[((-7,2),OD),((-6,2),OC),((-5,2),OQ)]
move3=[((4,-6),YD)]
b1=ap(board,move1); b2=ap(b1,move2); b3=ap(b2,move3)
print('--- red star (-2,5) score on bare board (after my crossx + her orange trio + my diamond) ---')
print('   red star @ (-2,5):', s1(b3,-2,5,RS), '  <-- her natural red-star value')
print()
print('--- Her move-4 options with hand {red star, orange crossx} (stars NOT yet on board) ---')
e=QwirkleEngine(); e.load_board_state(b3)
seen=set(); n=0
for s,p in generate_all_multi_moves(e,Counter([RS,OC])):
    k=frozenset(((x,y),t.color,t.shape) for (x,y),t in p)
    if k in seen: continue
    seen.add(k); n+=1
    print('   %2d  %s'%(s,'  '.join('(%d,%d)%s-%s'%(x,y,t.color[:3],t.shape) for (x,y),t in p)))
    if n>=10: break
print()
print('--- My FINALE: 3 stars {orange,blue,purple}, going out ---')
e=QwirkleEngine(); e.load_board_state(b3)
mm=generate_all_multi_moves(e,Counter([OS,BS,PS]))[0]
print('   if she did NOT play red star at (-2,5):  %d pts  %s'%(mm[0],'  '.join('(%d,%d)%s'%(x,y,t.color[:3]) for (x,y),t in mm[1])))
b4=ap(b3,[((-2,5),RS)])
e=QwirkleEngine(); e.load_board_state(b4)
mm2=generate_all_multi_moves(e,Counter([OS,BS,PS]))[0]
print('   if she DID play red star at (-2,5):      %d pts  %s'%(mm2[0],'  '.join('(%d,%d)%s'%(x,y,t.color[:3]) for (x,y),t in mm2[1])))
"

OUT
--- red star (-2,5) score on bare board (after my crossx + her orange trio + my diamond) ---
   red star @ (-2,5): 3   <-- her natural red-star value

--- Her move-4 options with hand {red star, orange crossx} (stars NOT yet on board) ---
    5  (6,9)red-star
    5  (6,-1)red-star
    4  (2,-9)ora-crossx
    4  (-3,-5)red-star
    4  (5,0)ora-crossx
    3  (-2,5)red-star
    3  (-4,-4)red-star
    3  (-1,6)red-star
    2  (-7,1)ora-crossx
    2  (-1,-5)red-star

--- My FINALE: 3 stars {orange,blue,purple}, going out ---
   if she did NOT play red star at (-2,5):  9 pts  (-2,6)blu  (-1,6)ora  (0,6)pur
   if she DID play red star at (-2,5):      11 pts  (-2,6)blu  (-1,6)ora  (0,6)pur
Good catch — you're right, and it exposed a flaw in how I presented the line. Here's the precise picture:

At (−2,5), the red star is naturally only 3 — just the horizontal y=5 run (red + yellow + blue stars). It showed as 5 in my line only because my move #3 had already dropped a blue star at (−2,6) directly above it, handing it a 2-point vertical. That ordering was a self-inflicted gift, and I shouldn't have presented it that way.

But — and this is why the verdict held at −3 — Jeanne doesn't need (−2,5). She has red-star spots worth 5 elsewhere, independent of anything I do:

red star at (6,−1) = 5 → extends the existing 4-star row (purple-yellow-green-orange at x=2..5) to five.
red star at (6,9) = 5.
So she banks 5 from her red star regardless. Still lose by 3 against best play.

The practical fix your question unlocks: play your 3 stars LAST, as the go-out — keep the yellow diamond for the middle instead. Then:

Your move order Result
If Jeanne plays the natural-looking red star at (−2,5) for 3 your finale stars score 11 (her tile now feeds your column) + 6 → you win 189–188
If Jeanne finds red star at (6,−1)/(6,9) for 5 finale stars = 9 + 6 → lose by 3
Same worst case (−3), but now there's a real trap instead of me gifting her the points. Let me update the record.

Edit C:\Users\Georg\.claude\plans\we-re-going-to-strategize-unified-bear.md
Modified
Edit C:\Users\Georg\.claude\plans\we-re-going-to-strategize-unified-bear.md
Added 6 lines
Record corrected. Net takeaway: the verdict is unchanged (lose by 3 vs. perfect play), but your instinct was right — (−2,5) is a 3-pointer, and there's no reason to gift Jeanne the extra 2.

Revised play order:

Now: green crossx (2,−7) + yellow crossx (2,−6) = 9.
Then: yellow diamond (4,−6) = 6 — hold your stars.
Last: the 3-star go-out at (−2,6)(−1,6)(0,6) — scores 9 normally, or 11 if she took the (−2,5) bait, plus the +6.
Your only losing leaks are Jeanne's orange-trio (8) and a red-star-5 at (6,−1)/(6,9). Both are non-obvious — the orange trio especially (far-left, stacking that square column). Make her find them.

Play the crossx pair, then tell me Jeanne's actual reply and I'll confirm whether she stayed on the optimal line or handed you the win.
