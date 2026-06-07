# Example of Claude (likely Opus 4.8) Q. code

cd c:/src/fun/qwirkle-solver && .venv/Scripts/python.exe -c "
import json
from collections import Counter
from qwirkle_core import Tile,QwirkleEngine,generate_all_multi_moves
d=json.load(open('game_state.json'))
board={(t['x'],t['y']):Tile(t['color'],t['shape']) for m in d['moves'] for t in m['tiles']}
def ap(b,pl):
    nb=dict(b)
    for (x,y),t in pl: nb[(x,y)]=t
    return nb
def best(b,hand,n=4):
    e=QwirkleEngine(); e.load_board_state(b)
    seen=set(); out=[]
    for s,p in generate_all_multi_moves(e,hand):
        k=frozenset(((x,y),t.color,t.shape) for (x,y),t in p)
        if k in seen: continue
        seen.add(k); out.append((s,p))
        if len(out)>=n: break
    return out
stars=Counter([Tile('orange','star'),Tile('blue','star'),Tile('purple','star')])
jh=Counter([Tile('red','star'),Tile('orange','square'),Tile('orange','crossx')])
YD=Tile('yellow','diamond')
b_d=ap(board,[((4,-6),YD)])   # ORDER B: diamond played first

print('1) Jeannes BEST after I play diamond first (does anything jump to >=8?):')
for s,p in best(b_d,jh,5):
    print('   %2d  %s'%(s,'  '.join('(%d,%d)%s-%s'%(x,y,t.color[:3],t.shape) for (x,y),t in p)))

print()
print('2) THE TRAP: if Jeanne then plays red star at (-2,5), my stars-last score:')
b_trap=ap(b_d,[((-2,5),Tile('red','star'))])
print('   my best star play:', best(b_trap,stars,1)[0][0],'pts ->', '  '.join('(%d,%d)%s'%(x,y,t.color[:3]) for (x,y),t in best(b_trap,stars,1)[0][1]))

print()
print('3) BLOCK TEST: if Jeanne plays red star at (-1,6) to wreck my star line:')
b_blk=ap(b_d,[((-1,6),Tile('red','star'))])
bb=best(b_blk,stars,3)
print('   her red star(-1,6) is legal & worth:', best(b_d,Counter([Tile('red','star')]),9999) and 'see below')
e=QwirkleEngine(); e.load_board_state(b_d)
print('   (legal for her at (-1,6)?', e.is_legal_move((-1,6),Tile('red','star')),', score', e.calculate_score((-1,6),Tile('red','star')) if e.is_legal_move((-1,6),Tile('red','star')) else 'NA',')')
print('   my fallback 3-star go-out still available:', bb[0][0],'pts ->','  '.join('(%d,%d)%s'%(x,y,t.color[:3]) for (x,y),t in bb[0][1]))
"