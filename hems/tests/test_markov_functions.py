import pytest
from ..markov_functions import markov_weekday, markov_weekend

@pytest.mark.parametrize("func", [markov_weekday, markov_weekend])
def test_markov_functions(func):
    min_soc, cd_rate, max_soc = 8.16, 6.6, 40
    availability, min_charge = func(min_soc, cd_rate)

    assert len(availability) == 48, f"{func.__name__} availability length should be 48"
    assert all(min_charge <= max_soc), f"Min charge in {func.__name__} should not exceed max_soc"
    assert all((availability == 0) <= (min_charge >= min_soc)), f"Min charge in {func.__name__} should not go below min_soc when the car is used"
