import numpy as np
from terrain import decode,tile
def test_signed_and_missing():
    a=decode([[[0,0,100],[255,255,156],[128,0,0]]])
    assert a[0,0]==1 and a[0,1]==-1 and np.isnan(a[0,2])
def test_sekigahara_tile():
    x,y=tile(136.47,35.36)
    assert 14400<x<14410 and 6460<y<6480
