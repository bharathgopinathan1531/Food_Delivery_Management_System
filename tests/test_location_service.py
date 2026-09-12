from app.services.location_service import calculate_distance


def test_calculate_distance():
    distance = calculate_distance(
        13.0827,
        80.2707,
        13.0674,
        80.2376,
    )

    assert distance > 0
    assert distance < 10


def test_same_location_distance_is_zero():
    distance = calculate_distance(
        13.0827,
        80.2707,
        13.0827,
        80.2707,
    )

    assert distance == 0