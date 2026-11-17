"""Справочники и универсальный медицинский переводчик для GUI сетевых калькуляторов."""

import json
import os
import re
import ssl
import urllib.parse
import urllib.request

_SSL_CTX = ssl._create_unverified_context()
_JSON_PATH = os.path.join(os.path.dirname(__file__), "clinical_phrases_ru.json")
_CATALOG_PATH = os.path.join(os.path.dirname(__file__), "network_tools_ru.json")

# Кэш переводов
_PHRASES_CACHE: dict[str, str] = {}
if os.path.exists(_JSON_PATH):
    try:
        with open(_JSON_PATH, "r", encoding="utf-8") as _f:
            _PHRASES_CACHE = json.load(_f)
    except Exception:
        _PHRASES_CACHE = {}

# Авторизованный каталог 152 клинических калькуляторов
NETWORK_TOOLS_RU: dict[str, dict] = {}
if os.path.exists(_CATALOG_PATH):
    try:
        with open(_CATALOG_PATH, "r", encoding="utf-8") as _f:
            NETWORK_TOOLS_RU = json.load(_f)
    except Exception:
        NETWORK_TOOLS_RU = {}


def _save_cache() -> None:
    try:
        with open(_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(_PHRASES_CACHE, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


# Клинические приоритетные переводы терминов
CLINICAL_OVERRIDES: dict[str, str] = {
    "confusion": "Нарушение сознания",
    "respiratory rate": "Частота дыхания (ЧДД)",
    "blood pressure": "Артериальное давление (АД)",
    "equation": "Формула",
    "yes": "Да",
    "no": "Нет",
    "male": "Мужской",
    "female": "Женский",
    "per sepsis-3: sofa ≥2 indicates organ dysfunction in suspected infection": "По критериям Sepsis-3: SOFA ≥ 2 указывает на органную дисфункцию при подозрении на инфекцию",
    "cardiology consultation strongly recommended": "Настоятельно рекомендуется консультация кардиолога",
    "consider non-invasive cardiac testing": "Рассмотрите возможность неинвазивного кардиологического исследования",
    "assess if surgery can be delayed or modified": "Оцените, можно ли отложить или изменить операцию",
    "optimize all cardiac medications": "Оптимизируйте все кардиологические препараты",
    "consider if coronary revascularization indicated first": "Рассмотреть, показана ли в первую очередь коронарная реваскуляризация",
    "intensive perioperative monitoring needed": "Необходим интенсивный периоперационный мониторинг",
    "cardiology consultation": "Консультация кардиолога",
    "functional or pharmacologic stress testing": "Функциональное или фармакологическое стресс-тестирование",
    "multidisciplinary surgical planning": "Мультидисциплинарное хирургическое планирование",
    "detailed informed consent discussion": "Подробное обсуждение информированного согласия",
}


def translate_any_text(text: str | None) -> str:
    """Универсальный переводчик любого текста на русский язык с кэшированием."""
    if not text:
        return ""
    stripped = text.strip()
    if not stripped:
        return ""

    # 0. Приоритетные клинические термины
    if stripped.lower() in CLINICAL_OVERRIDES:
        return CLINICAL_OVERRIDES[stripped.lower()]

    # 1. Проверяем точное совпадение в кэше
    if stripped in _PHRASES_CACHE:
        return _PHRASES_CACHE[stripped]

    # 2. Регистронезависимая проверка
    lower = stripped.lower()
    for k, v in _PHRASES_CACHE.items():
        if k.lower() == lower:
            return v

    # 3. Динамический перевод через Google Translate API с кэшированием
    try:
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=ru&dt=t&q={urllib.parse.quote(stripped)}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        resp = urllib.request.urlopen(req, context=_SSL_CTX, timeout=3).read().decode("utf-8")
        data = json.loads(resp)
        translated = "".join(chunk[0] for chunk in data[0] if chunk[0]).strip()
        if translated:
            _PHRASES_CACHE[stripped] = translated
            _save_cache()
            return translated
    except Exception:
        pass

    # 4. Запасные правила / шаблоны
    return _fallback_translate(stripped)


def _fallback_translate(text: str) -> str:
    replacements = [
        (r"\bCardiology consultation strongly recommended\b", "Настоятельно рекомендуется консультация кардиолога"),
        (r"\bConsider non-invasive cardiac testing\b", "Рассмотрите возможность неинвазивного кардиологического исследования"),
        (r"\bAssess if surgery can be delayed or modified\b", "Оцените, можно ли отложить или изменить операцию"),
        (r"\bOptimize all cardiac medications\b", "Оптимизируйте все кардиологические препараты"),
        (r"\bConsider if coronary revascularization indicated first\b", "Рассмотреть, показана ли в первую очередь коронарная реваскуляризация"),
        (r"\bIntensive perioperative monitoring needed\b", "Необходим интенсивный периоперационный мониторинг"),
        (r"\bCardiology consultation\b", "Консультация кардиолога"),
        (r"\bFunctional or pharmacologic stress testing\b", "Функциональное или фармакологическое стресс-тестирование"),
        (r"\bMultidisciplinary surgical planning\b", "Мультидисциплинарное хирургическое планирование"),
        (r"\bDetailed informed consent discussion\b", "Подробное обсуждение информированного согласия"),
        (r"\bHospital admission recommended\b", "Рекомендована госпитализация в стационар"),
        (r"\bHigh risk\b", "Высокий риск"),
        (r"\bModerate risk\b", "Умеренный риск"),
        (r"\bLow risk\b", "Низкий риск"),
        (r"\bSevere\b", "Тяжелая степень"),
        (r"\bmortality\b", "летальность"),
        (r"\bConfusion\b", "Нарушение сознания"),
        (r"\bRespiratory rate\b", "Частота дыхания"),
        (r"\bBlood pressure\b", "Артериальное давление"),
    ]
    res = text
    for pat, rep in replacements:
        res = re.sub(pat, rep, res, flags=re.IGNORECASE)
    return res


# Базовые русские названия для самых популярных калькуляторов
TOOL_TRANSLATIONS: dict[str, str] = {
    "ckd_epi_2021": "рСКФ CKD-EPI 2021 (креатинин, без расы)",
    "asa_physical_status": "Классификация физического статуса ASA",
    "mallampati_score": "Шкала Маллампати (оценка дыхательных путей)",
    "rcri": "Индекс сердечно-сосудистого риска Ли (RCRI)",
    "apache_ii": "Шкала APACHE II (тяжесть состояния в ОРИТ)",
    "rass": "Шкала седации и возбуждения Ричмонда (RASS)",
    "sofa_score": "Шкала SOFA (полиорганная недостаточность при сепсисе)",
    "sofa2_score": "Шкала SOFA-2 (консенсус 2025)",
    "qsofa_score": "Шкала qSOFA (быстрый скрининг сепсиса)",
    "news2_score": "Шкала раннего предупреждения NEWS2",
    "glasgow_coma_scale": "Шкала комы Глазго (GCS, уровень сознания)",
    "cam_icu": "Метод оценки спутанности сознания в ОРИТ (CAM-ICU)",
    "pediatric_dosing": "Педиатрический расчет дозирования лекарств",
    "mabl": "Максимально допустимая кровопотеря (MABL)",
    "transfusion_calc": "Калькулятор объема трансфузии крови",
    "curb65": "Шкала CURB-65 (тяжесть внебольничной пневмонии)",
    "chads2_vasc": "Шкала CHA₂DS₂-VASc (риск инсульта при ФП)",
    "chads2_va": "Шкала CHA₂DS₂-VA (рекомендации ESC 2024)",
    "heart_score": "Шкала HEART (риск при боли в груди)",
    "has_bled": "Шкала HAS-BLED (риск кровотечений при ФП)",
    "meld_score": "Шкала MELD (терминальная болезнь печени)",
    "meld_na": "Шкала MELD-Na",
    "child_pugh": "Шкала Чайлда — Пью (тяжесть цирроза)",
    "wells_dvt": "Критерии Уэллса для тромбоза глубоких вен (ТГВ)",
    "wells_pe": "Критерии Уэллса для ТЭЛА",
    "geneva_score": "Женевская шкала оценки риска ТЭЛА",
    "perc_rule": "Критерии исключения легочной эмболии (PERC)",
    "timi_stemi": "Шкала риска TIMI при STEMI",
    "timi_nstemi": "Шкала риска TIMI при NSTEMI",
    "grace_score": "Шкала GRACE (риск летальности при ОКС)",
    "crusade_score": "Шкала риска кровотечений CRUSADE",
    "four_score": "Шкала комы FOUR",
    "bap_65": "Шкала BAP-65 (обострение ХОБЛ)",
    "pesi_score": "Индекс тяжести ТЭЛА (PESI)",
    "spesi_score": "Упрощенный индекс тяжести ТЭЛА (sPESI)",
    "anion_gap": "Анионный интервал плазмы (Anion Gap)",
    "delta_gap": "Дельта-соотношение (Delta Gap)",
    "corrected_calcium": "Кальций скорректированный (по альбумину)",
    "corrected_sodium": "Натрий скорректированный (по глюкозе)",
    "fractional_excretion_na": "Фракционная экскреция натрия (FeNa)",
    "fractional_excretion_urea": "Фракционная экскреция мочевины (FeUrea)",
    "creatinine_clearance_cockcroft": "Клиренс креатинина Кокрофта — Голта",
    "stop_bang": "Опросник апноэ сна STOP-BANG",
    "centor_score": "Критерии Центора (фарингит группы А)",
    "alvarado_score": "Шкала Альварадо (острый аппендицит)",
    "bisap_score": "Шкала BISAP (тяжесть острого панкреатита)",
    "ranson_criteria": "Критерии Рэнсона (острый панкреатит)",
    "mrs_score": "Модифицированная шкала Рэнкина (mRS)",
    "nihss": "Шкала инсульта NIHSS",
    "bmi": "Индекс массы тела (ИМТ / BMI)",
    "bsa": "Площадь поверхности тела (BSA)",
    "bsa_mosteller": "Площадь поверхности тела Мостеллера",
    "qtc": "Корригированный интервал QT (QTc)",
}

# Клинические специальности
SPECIALTY_TRANSLATIONS: dict[str, str] = {
    "anesthesiology": "Анестезиология",
    "cardiac_anesthesia": "Кардиоанестезиология",
    "cardiology": "Кардиология",
    "critical_care": "Реанимация и интенсивная терапия (ОРИТ)",
    "emergency_medicine": "Неотложная помощь / Скорая помощь",
    "hematology": "Гематология",
    "hepatology": "Гепатология",
    "internal_medicine": "Терапия / Внутренние болезни",
    "nephrology": "Нефрология",
    "neurology": "Неврология",
    "pediatrics": "Педиатрия",
    "pulmonology": "Пульмонология",
    "surgery": "Хирургия",
    "infectious_disease": "Инфекционные болезни",
    "obstetrics": "Акушерство и гинекология",
    "endocrinology": "Эндокринология",
    "gastroenterology": "Гастроэнтерология",
    "oncology": "Онкология",
    "geriatrics": "Гериатрия",
    "toxicology": "Токсикология",
}

# Параметры шкал
PARAM_TRANSLATIONS: dict[str, str] = {
    "age": "Возраст пациента",
    "age_years": "Возраст пациента",
    "gender": "Пол пациента",
    "sex": "Пол пациента",
    "weight": "Масса тела (вес)",
    "weight_kg": "Масса тела",
    "height": "Рост",
    "height_cm": "Рост",
    "serum_creatinine": "Креатинин сыворотки крови",
    "creatinine": "Креатинин сыворотки крови",
    "systolic_bp": "Систолическое АД",
    "sbp": "Систолическое АД",
    "diastolic_bp": "Диастолическое АД",
    "dbp": "Диастолическое АД",
    "mean_arterial_pressure": "Среднее артериальное давление (САД)",
    "map": "Среднее артериальное давление (САД)",
    "heart_rate": "Частота сердечных сокращений (ЧСС / пульс)",
    "hr": "Частота сердечных сокращений (ЧСС)",
    "respiratory_rate": "Частота дыхания (ЧДД)",
    "rr": "Частота дыхания (ЧДД)",
    "temperature": "Температура тела",
    "fio2": "Фракция кислорода во вдыхаемой смеси (FiO₂, 0.21–1.0)",
    "pao2": "Парциальное давление кислорода (PaO₂)",
    "paco2": "Парциальное давление углекислого газа (PaCO₂)",
    "platelets": "Тромбоциты крови",
    "bilirubin": "Общий билирубин",
    "sodium": "Натрий сыворотки",
    "potassium": "Калий сыворотки",
    "albumin": "Альбумин сыворотки",
    "glucose": "Глюкоза крови",
    "bun": "Азот мочевины крови (BUN)",
    "urea": "Мочевина крови",
    "wbc": "Лейкоциты крови (WBC)",
    "hemoglobin": "Гемоглобин крови",
    "hgb": "Гемоглобин крови",
    "hematocrit": "Гематокрит",
    "hct": "Гематокрит",
    "inr": "МНО (Международное нормализованное отношение)",
    "confusion": "Нарушение сознания / дезориентация (новое появление)",
    "bun_gt_19_or_urea_gt_7": "Мочевина крови > 7 ммоль/л (или BUN > 19 мг/дл)",
    "respiratory_rate_gte_30": "Тахипноэ: частота дыхания ≥ 30 вдохов в минуту",
    "sbp_lt_90_or_dbp_lte_60": "Гипотензия: САД < 90 мм рт. ст. или ДАД ≤ 60 мм рт. ст.",
    "age_gte_65": "Возраст пациента 65 лет и старше",
    "high_risk_surgery": "Вмешательство высокого риска (торакальное, полостное или крупное сосудистое)",
    "ischemic_heart_disease": "Ишемическая болезнь сердца (ИБС) в анамнезе",
    "heart_failure": "Хроническая сердечная недостаточность (ХСН)",
    "cerebrovascular_disease": "Цереброваскулярная патология (инсульт или ТИА в анамнезе)",
    "insulin_diabetes": "Сахарный диабет на инсулинотерапии",
    "creatinine_above_2": "Предоперационный креатинин > 177 мкмоль/л (> 2.0 мг/дл)",
    "hypertension": "Артериальная гипертензия в анамнезе",
    "diabetes": "Сахарный диабет в анамнезе",
    "stroke_tia": "Инсульт, транзиторная ишемическая атака или эмболия в анамнезе",
    "vascular_disease": "Сосудистое заболевание (инфаркт миокарда, бляшки в аорте, атеросклероз)",
    "mechanical_ventilation": "Пациент находится на искусственной вентиляции легких (ИВЛ)",
    "vasopressor": "Терапия вазопрессорами (норадреналин, дофамин и др.)",
    "eye_response": "Открывание глаз (1–4)",
    "verbal_response": "Речевая реакция (1–5)",
    "motor_response": "Двигательная реакция (1–6)",
    "asa_class": "Класс физического статуса по ASA (1–6)",
    "is_emergency": "Экстренная операция",
    "rass_score": "Балл по шкале седации-возбуждения RASS (-5..+4)",
}

# Степени тяжести
SEVERITY_TRANSLATIONS: dict[str, str] = {
    "severe": "🔴 Высокий риск / Тяжёлая степень",
    "high": "🔴 Высокий риск",
    "critical": "🚨 Критическое состояние",
    "moderate": "🟠 Умеренный / Средний риск",
    "intermediate": "🟠 Промежуточный риск",
    "mild": "🟢 Легкая степень / Низкий риск",
    "low": "🟢 Низкий риск",
    "normal": "🟢 В пределах нормы",
}

# Единицы измерения
UNIT_TRANSLATIONS: dict[str, str] = {
    "points": "баллов",
    "point": "балл",
    "score": "баллов",
    "years": "лет",
    "year": "лет",
    "mL/min/1.73m²": "мл/мин/1,73 м²",
    "ml/min/1.73m2": "мл/мин/1,73 м²",
    "mL/min": "мл/мин",
    "ml/min": "мл/мин",
    "mg/dL": "мг/дл",
    "umol/L": "мкмоль/л",
    "µmol/L": "мкмоль/л",
    "mmol/L": "ммоль/л",
    "g/dL": "г/дл",
    "g/L": "г/л",
    "kg": "кг",
    "cm": "см",
    "m²": "м²",
    "m2": "м²",
    "mmHg": "мм рт. ст.",
    "bpm": "уд/мин",
    "breaths/min": "вдохов/мин",
    "days": "дней",
    "hours": "часов",
    "%": "%",
}


def translate_tool_name(tool_id: str, original_name: str) -> str:
    """Возвращает перевод названия инструмента."""
    if tool_id in NETWORK_TOOLS_RU and NETWORK_TOOLS_RU[tool_id].get("name"):
        return NETWORK_TOOLS_RU[tool_id]["name"]
    if tool_id in TOOL_TRANSLATIONS:
        return TOOL_TRANSLATIONS[tool_id]
    return translate_any_text(original_name)


def translate_tool_purpose(tool_id: str, original_purpose: str) -> str:
    """Возвращает перевод клинического назначения калькулятора."""
    if tool_id in NETWORK_TOOLS_RU and NETWORK_TOOLS_RU[tool_id].get("purpose"):
        return NETWORK_TOOLS_RU[tool_id]["purpose"]
    return translate_any_text(original_purpose)


def get_tool_keywords(tool_id: str) -> list[str]:
    """Возвращает список ключевых слов поиска для калькулятора."""
    if tool_id in NETWORK_TOOLS_RU:
        return NETWORK_TOOLS_RU[tool_id].get("keywords", [])
    return []


def translate_specialty(spec: str) -> str:
    """Возвращает русское название медицинской специальности."""
    return SPECIALTY_TRANSLATIONS.get(spec.lower(), translate_any_text(spec.replace("_", " ")))


def translate_param_name(param_name: str, original_desc: str = "") -> str:
    """Возвращает русский лейбл параметра для формы."""
    clean_name = param_name.lower().strip()
    if clean_name in PARAM_TRANSLATIONS:
        return PARAM_TRANSLATIONS[clean_name]

    if original_desc and original_desc.lower() != param_name.lower():
        return translate_any_text(original_desc)

    return translate_any_text(param_name.replace("_", " "))


def translate_severity(severity: str) -> str:
    """Возвращает русское обозначение степени тяжести."""
    return SEVERITY_TRANSLATIONS.get(severity.lower(), translate_any_text(severity))


def translate_unit(unit: str) -> str:
    """Возвращает русское обозначение единицы измерения."""
    return UNIT_TRANSLATIONS.get(unit, unit)


def translate_component_label(label: str) -> str:
    """Переводит подписи компонентов в таблице результатов."""
    return translate_any_text(label)


def translate_summary(summary: str | None) -> str:
    """Переводит текст резюме / интерпретации результата на русский язык."""
    return translate_any_text(summary)


def translate_recommendations(rec_input: str | list | None) -> list[str]:
    """Переводит строку или список клинических рекомендаций на русский язык."""
    if not rec_input:
        return []

    if isinstance(rec_input, list):
        raw_items = [str(x).strip() for x in rec_input if str(x).strip()]
    else:
        raw_items = [s.strip() for s in re.split(r"[;\n]+", str(rec_input)) if s.strip()]

    translated_list: list[str] = []
    for item in raw_items:
        translated_list.append(translate_any_text(item))

    return translated_list
