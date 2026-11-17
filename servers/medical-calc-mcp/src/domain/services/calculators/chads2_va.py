# Медицинские калькуляры, используются для обучения технологиям MCP
# для слушателей курса 'Программная инженерия мультиагентных систем клинической медицины'
# Иннополис, осень 2026

"""
CHA₂DS₂-VA Score Calculator (2024 ESC Guidelines)

Updated stroke risk assessment for atrial fibrillation that removes sex
as a risk modifier, as per the 2024 ESC Guidelines for AF management.

2024 ESC Guideline Reference:
    Van Gelder IC, Rienstra M, Bunting KV, et al. 2024 ESC Guidelines for
    the management of atrial fibrillation developed in collaboration with
    EACTS. Eur Heart J. 2024;45(36):3314-3414.
    doi:10.1093/eurheartj/ehae176. PMID: 39217497.

Key Change from CHA₂DS₂-VASc:
    - Removed "Sc" (Sex category - female) as a risk modifier
    - Maximum score reduced from 9 to 8
    - Sex-neutral thresholds for anticoagulation decisions
"""

from ...entities.score_result import ScoreResult
from ...entities.tool_metadata import ToolMetadata
from ...value_objects.interpretation import Interpretation, RiskLevel, Severity
from ...value_objects.reference import Reference
from ...value_objects.tool_keys import (
    ClinicalContext,
    HighLevelKey,
    LowLevelKey,
    Specialty,
)
from ...value_objects.units import Unit
from ..base import BaseCalculator


class Chads2VaCalculator(BaseCalculator):
    """
    CHA₂DS₂-VA Score for Atrial Fibrillation Stroke Risk (2024 ESC)

    2024 ESC Guidelines removed sex as a risk modifier because:
    - Female sex alone does not increase stroke risk without other factors
    - Avoids gender-based treatment disparities
    - Simplifies clinical decision-making

    Scoring criteria:
    - Congestive Heart Failure: +1
    - Hypertension: +1
    - Age ≥75 years: +2
    - Diabetes mellitus: +1
    - Stroke/TIA/TE history: +2
    - Vascular disease (prior MI, PAD, aortic plaque): +1
    - Age 65-74 years: +1

    Maximum score: 8

    Anticoagulation recommendations (2024 ESC guidelines):
    - Score 0: No anticoagulation (very low risk)
    - Score 1: Anticoagulation should be considered
    - Score ≥2: Anticoagulation is recommended

    CHA₂DS₂-VA шкала оценки риска инсульта (рекомендации ESC 2024 по фибрилляции предсердий)

    Рекомендации ESC 2024 исключили пол как модификатор риска:
    - Женский пол сам по себе без других факторов не увеличивает риск инсульта
    - Устранение различий в лечении по признаку пола
    - Упрощение принятия клинических решений
    """

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            low_level=LowLevelKey(
                tool_id="chads2_va",
                name="CHA₂DS₂-VA Score (2024 ESC)",
                purpose="Estimate stroke risk in AF using 2024 ESC sex-neutral criteria for anticoagulation decisions",
                input_params=[
                    "chf_or_lvef_lte_40",
                    "hypertension",
                    "age_gte_75",
                    "diabetes",
                    "stroke_tia_or_te_history",
                    "vascular_disease",
                    "age_65_to_74",
                ],
                output_type="Score 0-8 with annual stroke risk and anticoagulation recommendation",
            ),
            high_level=HighLevelKey(
                specialties=(
                    Specialty.CARDIOLOGY,
                    Specialty.NEUROLOGY,
                    Specialty.INTERNAL_MEDICINE,
                    Specialty.EMERGENCY_MEDICINE,
                ),
                conditions=(
                    "atrial fibrillation",
                    "AF",
                    "Afib",
                    "atrial flutter",
                    "stroke prevention",
                    "thromboembolism",
                ),
                clinical_contexts=(
                    ClinicalContext.RISK_STRATIFICATION,
                    ClinicalContext.TREATMENT_DECISION,
                    ClinicalContext.PROGNOSIS,
                ),
                clinical_questions=(
                    "Does this AF patient need anticoagulation per 2024 ESC guidelines?",
                    "What is the stroke risk using the new CHA₂DS₂-VA score?",
                    "Should I prescribe a DOAC for this AF patient (2024 criteria)?",
                    "Is anticoagulation indicated using sex-neutral criteria?",
                    "What is the CHA₂DS₂-VA score without sex modifier?",
                ),
                icd10_codes=(
                    "I48",  # Atrial fibrillation and flutter
                    "I48.0",  # Paroxysmal atrial fibrillation
                    "I48.1",  # Persistent atrial fibrillation
                    "I48.2",  # Chronic atrial fibrillation
                    "I48.91",  # Unspecified atrial fibrillation
                ),
                keywords=(
                    "CHA2DS2-VA",
                    "CHADS-VA",
                    "2024 ESC",
                    "ESC 2024",
                    "sex-neutral",
                    "atrial fibrillation stroke risk",
                    "anticoagulation AF",
                    "stroke prevention AF",
                    "DOAC indication",
                    "новая версия",
                    "фибрилляция предсердий",
                    "антикоагулянты",
                ),
            ),
            references=(
                Reference(
                    citation="Van Gelder IC, Rienstra M, Bunting KV, et al. 2024 ESC Guidelines "
                    "for the management of atrial fibrillation developed in collaboration "
                    "with EACTS. Eur Heart J. 2024;45(36):3314-3414.",
                    doi="10.1093/eurheartj/ehae176",
                    pmid="39217497",
                    year=2024,
                ),
                Reference(
                    citation="Lip GY, Nieuwlaat R, Pisters R, et al. Refining clinical risk "
                    "stratification for predicting stroke and thromboembolism in atrial "
                    "fibrillation using a novel risk factor-based approach: the euro "
                    "heart survey on atrial fibrillation. Chest. 2010;137(2):263-272.",
                    doi="10.1378/chest.09-1584",
                    pmid="19762550",
                    year=2010,
                ),
            ),
            version="1.0.0",
            validation_status="validated",
        )

    def calculate(
        self,
        chf_or_lvef_lte_40: bool,
        hypertension: bool,
        age_gte_75: bool,
        diabetes: bool,
        stroke_tia_or_te_history: bool,
        vascular_disease: bool,
        age_65_to_74: bool,
    ) -> ScoreResult:
        """
        Calculate CHA₂DS₂-VA score (2024 ESC - sex-neutral version).
        Расчет шкалы CHA₂DS₂-VA (ESC 2024 - версия без учета пола)

        Args:
            chf_or_lvef_lte_40: CHF or LVEF ≤40% / ХСН или ФВЛЖ ≤40%
            hypertension: History of hypertension / Артериальная гипертензия в анамнезе
            age_gte_75: Age ≥75 years (2 points) / Возраст ≥75 лет (2 балла)
            diabetes: Diabetes mellitus / Сахарный диабет
            stroke_tia_or_te_history: Prior stroke, TIA, or thromboembolism (2 points) /
                                       Инсульт, ТИА или тромбоэмболия в анамнезе (2 балла)
            vascular_disease: Prior MI, PAD, or aortic plaque /
                              Инфаркт миокарда, заболевание периферических артерий или атеросклеротическая бляшка аорты
            age_65_to_74: Age 65-74 years (1 point; mutually exclusive with age ≥75) /
                          Возраст 65-74 года (1 балл; взаимоисключающий с возрастом ≥75)

        Returns:
            ScoreResult with score, stroke risk, and anticoagulation recommendation
        """
        # Calculate score (no sex modifier in 2024 version)
        score = 0
        score += 1 if chf_or_lvef_lte_40 else 0
        score += 1 if hypertension else 0
        score += 2 if age_gte_75 else 0
        score += 1 if diabetes else 0
        score += 2 if stroke_tia_or_te_history else 0
        score += 1 if vascular_disease else 0
        score += 1 if age_65_to_74 and not age_gte_75 else 0  # Only if not ≥75

        # Determine interpretation
        interpretation = self._interpret_score(score)

        # Component details
        components = {
            "C - CHF/LVEF ≤40% (ХСН/ФВЛЖ ≤40%)": 1 if chf_or_lvef_lte_40 else 0,
            "H - Hypertension (Артериальная гипертензия)": 1 if hypertension else 0,
            "A₂ - Age ≥75 (Возраст ≥75 лет)": 2 if age_gte_75 else 0,
            "D - Diabetes (Сахарный диабет)": 1 if diabetes else 0,
            "S₂ - Stroke/TIA/TE (Анамнез инсульта/ТИА/ТЭ)": 2 if stroke_tia_or_te_history else 0,
            "V - Vascular disease (Сосудистые заболевания)": 1 if vascular_disease else 0,
            "A - Age 65-74 (Возраст 65-74 года)": 1 if (age_65_to_74 and not age_gte_75) else 0,
        }

        return ScoreResult(
            tool_name=self.low_level_key.name,
            tool_id=self.low_level_key.tool_id,
            value=score,
            unit=Unit.SCORE,
            interpretation=interpretation,
            calculation_details=components,
            references=list(self.references),
        )

    def _interpret_score(self, score: int) -> Interpretation:
        """
        Generate interpretation based on CHA₂DS₂-VA score per 2024 ESC guidelines.
        Интерпретация балла CHA₂DS₂-VA согласно клиническим рекомендациям ESC 2024
        """

        # Annual stroke risk rates (estimated from original CHA₂DS₂-VASc data,
        # adjusted for sex-neutral scoring)
        stroke_rates = {
            0: "0.2%",
            1: "0.6%",
            2: "2.2%",
            3: "3.2%",
            4: "4.8%",
            5: "7.2%",
            6: "9.7%",
            7: "11.2%",
            8: "14.5%",
        }

        annual_risk = stroke_rates.get(score, ">14%")

        if score == 0:
            # Very low risk - no anticoagulation
            severity = Severity.NORMAL
            risk_level = RiskLevel.VERY_LOW
            summary = f"CHA₂DS₂-VA = {score}: Very low risk ({annual_risk} annual stroke risk)"
            detail = f"Very low stroke risk per 2024 ESC guidelines. Annual ischemic stroke rate approximately {annual_risk}. No anticoagulation recommended."
            detail_zh = f"По рекомендациям ESC 2024 риск инсульта очень низкий. Годовой риск ~{annual_risk}. Антикоагуляция не рекомендуется."
            recommendations = [
                "No anticoagulation recommended (Антикоагуляция не рекомендуется)",
                "Address modifiable cardiovascular risk factors",
                "Reassess risk factors periodically",
            ]
            next_steps = [
                "Контроль модифицируемых факторов риска (АД, гликемия)",
                "Периодическая переоценка риска по шкале CHA₂DS₂-VA",
                "Коррекция образа жизни для снижения сердечно-сосудистого риска",
            ]

        elif score == 1:
            # Low risk - consider anticoagulation
            severity = Severity.MILD
            risk_level = RiskLevel.LOW
            summary = f"CHA₂DS₂-VA = {score}: Low risk ({annual_risk} annual stroke risk)"
            detail = (
                f"Low stroke risk per 2024 ESC guidelines. "
                f"Annual stroke rate approximately {annual_risk}. "
                f"Anticoagulation should be considered based on individual assessment."
            )
            detail_zh = f"По рекомендациям ESC 2024 риск инсульта низкий. Годовой риск ~{annual_risk}. Следует рассмотреть прием антикоагулянтов индивидуально."
            recommendations = [
                "Anticoagulation should be considered (Следует рассмотреть прием антикоагулянтов)",
                "Assess bleeding risk with HAS-BLED score",
                "Shared decision-making with patient",
                "DOACs preferred over VKA if OAC chosen",
            ]
            next_steps = [
                "Оценка риска кровотечения по шкале HAS-BLED",
                "Совместное принятие решения с пациентом, обсуждение рисков и пользы",
                "При назначении антикоагулянтов предпочтение отдается ПОАК (DOAC)",
                "Устранение модифицируемых факторов риска кровотечения",
            ]

        else:
            # Score ≥2: Anticoagulation recommended
            if score <= 3:
                severity = Severity.MODERATE
                risk_level = RiskLevel.INTERMEDIATE
            elif score <= 5:
                severity = Severity.SEVERE
                risk_level = RiskLevel.HIGH
            else:
                severity = Severity.CRITICAL
                risk_level = RiskLevel.VERY_HIGH

            summary = f"CHA₂DS₂-VA = {score}: {risk_level.value.replace('_', ' ').title()} risk ({annual_risk} annual stroke risk)"
            detail = (
                f"{'Significant' if score <= 4 else 'High'} stroke risk per 2024 ESC guidelines. "
                f"Annual stroke rate approximately {annual_risk}. "
                f"Oral anticoagulation is recommended."
            )
            detail_zh = f"По рекомендациям ESC 2024 риск инсульта {'умеренный' if score <= 3 else 'высокий'}. Годовой риск ~{annual_risk}. Рекомендуется прием пероральных антикоагулянтов."
            recommendations = [
                "Oral anticoagulation is recommended (Рекомендуется пероральная антикоагулянтная терапия)",
                "DOACs preferred over VKA (except mechanical valves, moderate-severe MS)",
                "Aspirin monotherapy is NOT adequate for stroke prevention",
            ]
            next_steps = [
                "Оценка функции почек для подбора дозировки ПОАК",
                "Оценка риска кровотечений по HAS-BLED и устранение факторов риска",
                "Выбор ПОАК с учетом клинических характеристик пациента",
                "Обучение пациента и обеспечение приверженности приему антикоагулянтов",
            ]

            if score >= 4:
                recommendations.append("High stroke risk - ensure OAC adherence (Высокий риск инсульта - обеспечить приверженность терапии)")
            if score >= 6:
                recommendations.append("Very high risk - consider cardiology consultation")

        return Interpretation(
            summary=summary,
            severity=severity,
            detail=f"{detail}\n\n{detail_zh}",
            stage=f"CHA₂DS₂-VA = {score}",
            stage_description=f"Annual stroke risk: {annual_risk} | Годовой риск инсульта: {annual_risk}",
            risk_level=risk_level,
            recommendations=tuple(recommendations),
            next_steps=tuple(next_steps),
            warnings=("High stroke risk - anticoagulation strongly recommended (Высокий риск инсульта - настоятельно рекомендуется антикоагуляция)",) if score >= 4 else tuple(),
        )
