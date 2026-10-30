from enum import Enum


CREATININE_UMOL_PER_MG_DL = 88.4


class Sex(str, Enum):
    female = "female"
    male = "male"


class CreatinineUnit(str, Enum):
    umol_l = "umol_l"
    mg_dl = "mg_dl"


def creatinine_to_mg_dl(value: float, unit: CreatinineUnit) -> float:
    if unit == CreatinineUnit.mg_dl:
        return value
    return value / CREATININE_UMOL_PER_MG_DL


def require_creatinine_mg_dl(value: float, unit: CreatinineUnit) -> float:
    mg_dl = creatinine_to_mg_dl(value, unit)
    if mg_dl < 0.05 or mg_dl > 40:
        raise ValueError(
            "Креатинин вне допустимого диапазона: 0,05–40 мг/дл "
            "(4,4–3536 мкмоль/л). Проверьте число и единицу измерения."
        )
    return mg_dl
