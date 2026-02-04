import numpy as np

from processing.line_detector import LineDetector

def test_line_detector_logic():
    ld = LineDetector()
    
    # Simulate lines: x = my + c
    # Let's assume a strictly rectangular court for simplicity (m=0 for vertical lines in x=my+c form essentially, but actually x constant means m=0)
    # x = 0*y + c => x = c
    
    # Lines at x=0, x=10, x=90, x=100
    # Outer Left: x=0
    # Inner Left: x=10
    # Inner Right: x=90
    # Outer Right: x=100
    
    # We need to simulate the 'detect_lines' internal logic or just populate the dict manually.
    # To test 'is_point_in_bounds', we can populate manually.
    
    ld.court_lines['outer_sidelines'] = [(0, 0), (0, 100)] # m=0, c=0; m=0, c=100
    ld.court_lines['inner_sidelines'] = [(0, 10), (0, 90)] # m=0, c=10; m=0, c=90
    
    # Baselines: y = mx + c
    # y = 0*x + 0 => y=0 (Top)
    # y = 0*x + 200 => y=200 (Bottom)
    ld.court_lines['baselines'] = [(0, 0), (0, 200)]
    
    # Test Point in Alley (x=5, y=100)
    # Singles: Should be OUT (5 < 10)
    # Doubles: Should be IN (5 > 0)
    
    print("\n--- Testing Point in Alley (5, 100) ---")
    singles_alley = ld.is_point_in_bounds((5, 100), mode="singles", shot_type="rally")
    doubles_alley = ld.is_point_in_bounds((5, 100), mode="doubles", shot_type="rally")
    
    print(f"Singles (Expect False): {singles_alley}")
    print(f"Doubles (Expect True): {doubles_alley}")
    
    assert singles_alley == False
    assert doubles_alley == True
    
    # Test Point in Center (x=50, y=100)
    print("\n--- Testing Point in Center (50, 100) ---")
    singles_center = ld.is_point_in_bounds((50, 100), mode="singles", shot_type="rally")
    doubles_center = ld.is_point_in_bounds((50, 100), mode="doubles", shot_type="rally")
    
    print(f"Singles (Expect True): {singles_center}")
    print(f"Doubles (Expect True): {doubles_center}")
    
    assert singles_center == True
    assert doubles_center == True
    
    # Test Point Out (x=-5, y=100)
    print("\n--- Testing Point Out (-5, 100) ---")
    doubles_out = ld.is_point_in_bounds((-5, 100), mode="doubles", shot_type="rally")
    print(f"Doubles (Expect False): {doubles_out}")
    assert doubles_out == False

if __name__ == "__main__":
    try:
        test_line_detector_logic()
        print("\nAll tests passed!")
    except AssertionError as e:
        print("\nTest failed!")
        # raise e
