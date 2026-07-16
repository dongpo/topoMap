from nma.geometry import line_self_intersects


def test_self_intersection_detection() -> None:
    assert line_self_intersects([[0, 0], [2, 2], [0, 2], [2, 0]])
    assert not line_self_intersects([[0, 0], [1, 1], [2, 1]])
