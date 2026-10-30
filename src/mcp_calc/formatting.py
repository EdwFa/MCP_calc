from decimal import ROUND_HALF_UP, Decimal


def round_half_up(value: float, digits: int) -> float:
    quantum = Decimal("1").scaleb(-digits)
    rounded = Decimal(str(value)).quantize(quantum, rounding=ROUND_HALF_UP)
    if digits == 0:
        return float(int(rounded))
    return float(rounded)


def format_rounded(value: float, digits: int) -> tuple[float, str]:
    rounded = round_half_up(value, digits)
    if digits == 0:
        return rounded, str(int(rounded))
    return rounded, f"{rounded:.{digits}f}"


def plural_points(score: int) -> str:
    remainder = abs(score) % 100
    last_digit = remainder % 10
    if 11 <= remainder <= 14:
        return "баллов"
    if last_digit == 1:
        return "балл"
    if 2 <= last_digit <= 4:
        return "балла"
    return "баллов"
