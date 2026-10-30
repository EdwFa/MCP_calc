import math

from pydantic import Field

from mcp_calc.domain import Sex
from mcp_calc.formatting import format_rounded
from mcp_calc.models import CalculatorResult, Component, InputModel
from mcp_calc.results import make_result


class QtcInput(InputModel):
    qt_ms: int = Field(ge=200, le=800)
    heart_rate_bpm: int = Field(ge=30, le=250)
    sex: Sex


def qtc_band(qtc_ms: int, sex: Sex) -> str:
    if qtc_ms >= 500:
        return "выраженно удлинённый"
    cutoff = 460 if sex == Sex.female else 450
    if qtc_ms >= cutoff:
        return "удлинённый"
    if qtc_ms <= 350:
        return "укороченный"
    return "в пределах этих порогов"


def compute_qtc(data: QtcInput) -> CalculatorResult:
    rr_seconds = 60 / data.heart_rate_bpm
    bazett_raw = data.qt_ms / math.sqrt(rr_seconds)
    fridericia_raw = data.qt_ms / (rr_seconds ** (1 / 3))
    bazett = int(format_rounded(bazett_raw, 0)[0])
    fridericia = int(format_rounded(fridericia_raw, 0)[0])
    bazett_band = qtc_band(bazett, data.sex)
    fridericia_band = qtc_band(fridericia, data.sex)
    cutoff = "≥460 мс для женщины" if data.sex == Sex.female else "≥450 мс для мужчины"
    interpretation = (
        f"Bazett {bazett} мс — {bazett_band}; Fridericia {fridericia} мс — {fridericia_band}. "
        f"Порог удлинения AHA/ACC: {cutoff}. Выраженное удлинение — ≥500 мс. "
        "Значение ≤350 мс ниже учебного порога укороченного QT."
    )
    if bazett_band != fridericia_band:
        interpretation += (
            " Формулы попали в разные категории: при пульсе далеко от 60 уд/мин Bazett смещает QTc сильнее."
        )
    return make_result(
        "qtc",
        precise=float(bazett),
        digits=0,
        unit="мс по Bazett",
        interpretation=interpretation,
        inputs=data,
        components=[
            Component(label="Интервал RR", value=f"{rr_seconds:.3f} с"),
            Component(label="QTc Bazett", value=f"{bazett} мс — {bazett_band}"),
            Component(label="QTc Fridericia", value=f"{fridericia} мс — {fridericia_band}"),
        ],
    )
