import datetime

from utils.validation.age_validators import validate_minimum_age


def _date_years_ago(today: datetime.date, years: int) -> datetime.date:
    try:
        return today.replace(year=today.year - years)
    except ValueError:
        # Handle leap day: roll to Feb 28
        return today.replace(year=today.year - years, day=28)


def test_validate_minimum_age_exactly_18():
    today = datetime.date.today()
    dob = _date_years_ago(today, 18)
    r = validate_minimum_age(dob, minimum_age=18)
    assert r.is_valid is True


def test_validate_minimum_age_under_18():
    today = datetime.date.today()
    dob_18 = _date_years_ago(today, 18)
    dob_under = dob_18 + datetime.timedelta(days=1)
    r = validate_minimum_age(dob_under, minimum_age=18)
    assert r.is_valid is False
    assert "at least 18" in (r.reason or "")


def test_validate_minimum_age_future_dob():
    future = datetime.date.today() + datetime.timedelta(days=1)
    r = validate_minimum_age(future, minimum_age=18)
    assert r.is_valid is False
    assert "cannot be in the future" in (r.reason or "")
