from OCC.Core.TopAbs import (TopAbs_FORWARD, TopAbs_REVERSED, TopAbs_INTERNAL, TopAbs_EXTERNAL)

def orientation_to_sense(orientation):
    # I think the orientation flags might actually indicate
    # TopAbs_FORWARD = 0
    # TopAbs_REVERSED = 1 	
    # TopAbs_INTERNAL = 2 	
    # TopAbs_EXTERNAL = 3
    assert orientation == TopAbs_FORWARD or orientation == TopAbs_REVERSED
    return orientation == TopAbs_FORWARD