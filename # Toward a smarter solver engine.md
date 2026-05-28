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
