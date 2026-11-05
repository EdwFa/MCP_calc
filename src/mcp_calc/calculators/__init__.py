from mcp_calc.calculators.bmi import BmiInput, compute_bmi
from mcp_calc.calculators.bsa import BsaInput, compute_bsa
from mcp_calc.calculators.cha2ds2_vasc import Cha2ds2VascInput, compute_cha2ds2_vasc
from mcp_calc.calculators.cockcroft_gault import CockcroftGaultInput, compute_cockcroft_gault
from mcp_calc.calculators.curb65 import Curb65Input, compute_curb65
from mcp_calc.calculators.egfr import EgfrInput, compute_egfr
from mcp_calc.calculators.qtc import QtcInput, compute_qtc
from mcp_calc.calculators.body_fat_navy import BodyFatNavyInput, compute_body_fat_navy

INPUT_MODELS = {
    "bmi": BmiInput,
    "bsa_mosteller": BsaInput,
    "egfr_ckd_epi_2021": EgfrInput,
    "cockcroft_gault": CockcroftGaultInput,
    "cha2ds2_vasc": Cha2ds2VascInput,
    "curb65": Curb65Input,
    "qtc": QtcInput,
    "body_fat_navy": BodyFatNavyInput,
}

COMPUTE = {
    "bmi": compute_bmi,
    "bsa_mosteller": compute_bsa,
    "egfr_ckd_epi_2021": compute_egfr,
    "cockcroft_gault": compute_cockcroft_gault,
    "cha2ds2_vasc": compute_cha2ds2_vasc,
    "curb65": compute_curb65,
    "qtc": compute_qtc,
    "body_fat_navy": compute_body_fat_navy,
}
