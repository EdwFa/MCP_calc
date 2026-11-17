import glob
import re

HEADER = """# Медицинские калькуляры, используются для обучения технологиям MCP
# для слушателей курса 'Программная инженерия мультиагентных систем клинической медицины'
# Иннополис, осень 2026

"""

aims65_replacements = {
    '上消化道出血死亡率預測工具，使用5個簡單指標。\n適用於急診快速風險分層。':
        'Инструмент прогнозирования летальности при кровотечениях из верхних отделов ЖКТ по 5 простым критериям.\nПрименяется для быстрой стратификации риска в отделении неотложной помощи.',
    '簡便的上消化道出血死亡率預測工具，僅需 5 項臨床指標。\n    命名來自五項指標的首字母: Albumin, INR, Mental status, SBP, age ≥65\n\n    評分範圍: 0-5 分':
        'Простой инструмент оценки риска госпитальной летальности при кровотечениях из верхних отделов ЖКТ (5 клинических критериев).\n    Название образовано от первых букв критериев: Albumin, INR, Mental status, SBP, age ≥65.\n\n    Диапазон оценки: 0-5 баллов',
}

apgar_replacements = {
    'APGAR Score Calculator - 新生兒評估量表':
        'APGAR Score Calculator - Шкала оценки состояния новорожденного по Апгар',
}

euroscore_replacements = {
    '歐洲心臟手術風險評估系統 II 版。\n用於預測心臟手術的院內死亡率。':
        'Европейская система оценки риска кардиохирургических операций (версия II).\nИспользуется для прогнозирования госпитальной летальности при операциях на сердце.',
    '計算心臟手術的預測死亡率。\n    基於患者因素、心臟狀態和手術因素的 Logistic 回歸模型。':
        'Расчет прогнозируемой госпитальной летальности при операциях на сердце.\n    Логистическая регрессионная модель на основе факторов пациента, состояния сердца и характера операции.',
}

glasgow_replacements = {
    '上消化道出血風險分層工具，預測是否需要內視鏡干預或輸血。\nESGE 指引推薦作為 UGIB 首選評估工具。':
        'Инструмент стратификации риска при кровотечениях из верхних отделов ЖКТ (потребность в эндоскопическом гемостазе или трансфузии).\nРекомендован клиническими рекомендациями ESGE как предпочтительный инструмент при ЖКК.',
    '上消化道出血風險評估工具，預測需要干預（輸血、內視鏡、手術）的風險。\n    GBS = 0 表示低風險，可考慮門診處理。\n\n    評分範圍: 0-23 分':
        'Оценка риска при желудочно-кишечных кровотечениях (потребность в гемотрансфузии, эндоскопии, хирургическом лечении).\n    GBS = 0 означает низкий риск, возможно амбулаторное лечение.\n\n    Диапазон оценки: 0-23 балла',
}

iss_replacements = {
    '創傷嚴重度評估工具，是創傷登錄和研究的國際標準。\n基於 Abbreviated Injury Scale (AIS) 計算。':
        'Инструмент оценки тяжести травмы (ISS) — международный стандарт для травматологических регистров и исследований.\nРассчитывается на основе сокращенной шкалы повреждений AIS (Abbreviated Injury Scale).',
}

lille_replacements = {
    '評估酒精性肝炎患者對類固醇治療7天後的反應。\n用於決定是否繼續或停止類固醇治療。':
        'Оценка ответа пациентов с острым алкогольным гепатитом на терапию кортикостероидами через 7 дней.\nИспользуется для принятия решения о продолжении или отмене кортикостероидной терапии.',
    '計算酒精性肝炎患者對類固醇治療7天後的反應。\n\n    輸出:\n    - Lille score 0-1\n    - Lille < 0.45: 響應者 (繼續類固醇)\n    - Lille ≥ 0.45: 非響應者 (停止類固醇)':
        'Расчет терапевтического ответа на кортикостероиды при остром алкогольном гепатите.\n\n    Результат:\n    - Балл Lille 0-1\n    - Lille < 0.45: ответчики (продолжать терапию стероидами)\n    - Lille ≥ 0.45: неответчики (отменить терапию стероидами)',
}

maddrey_replacements = {
    '用於評估酒精性肝炎的嚴重程度和預後。\nmDF ≥ 32 表示嚴重酒精性肝炎，考慮類固醇治療。':
        'Оценка степени тяжести и прогноза при алкогольном гепатите.\nmDF ≥ 32 указывает на тяжелое течение алкогольного гепатита, рекомендовано рассмотреть кортикостероидную терапию.',
    '計算公式:\n    mDF = 4.6 × (patient PT - control PT) + total bilirubin\n\n    臨床意義:\n    - mDF < 32: 輕至中度，死亡率 < 10%\n    - mDF ≥ 32: 嚴重，死亡率 30-50%，考慮類固醇治療':
        'Формула расчета:\n    mDF = 4.6 × (ПВ пациента - контрольное ПВ) + общий билирубин\n\n    Клиническое значение:\n    - mDF < 32: легкая или умеренная тяжесть, летальность < 10%\n    - mDF ≥ 32: тяжелое течение, летальность 30-50%, рассмотреть кортикостероиды',
}

pediatric_sofa_replacements = {
    'Pediatric SOFA (pSOFA) Score Calculator - 兒童器官衰竭評估':
        'Pediatric SOFA (pSOFA) Score Calculator - Оценка органной дисфункции у детей',
}

rts_replacements = {
    '生理性創傷評分系統，用於院前和急診創傷分流。\n結合 GCS、收縮壓和呼吸速率評估生理功能。':
        'Физиологическая шкала тяжести травмы для догоспитальной и экстренной сортировки.\nОценивает физиологическое состояние по ШКГ, систолическому АД и частоте дыхания.',
    '生理性創傷嚴重度評估，用於院前分流和預後預測。\n\n    三項生理參數:\n    - Glasgow Coma Scale (GCS)\n    - Systolic Blood Pressure (SBP)\n    - Respiratory Rate (RR)\n\n    評分範圍: 0-7.8408 (weighted) 或 0-12 (coded)':
        'Оценка физиологической тяжести травмы для догоспитальной сортировки и прогнозирования исходов.\n\n    Три физиологических параметра:\n    - Шкала комы Глазго (GCS)\n    - Систолическое АД (САД)\n    - Частота дыхания (ЧДД)\n\n    Диапазон оценки: 0-7.8408 (взвешенный) или 0-12 (кодированный)',
}

spesi_replacements = {
    '簡化版肺栓塞嚴重度指數，用於評估急性肺栓塞30天死亡風險。\n比原始 PESI 更簡單，僅需6個臨床變數。':
        'Упрощенный индекс тяжести тромбоэмболии легочной артерии (sPESI) для оценки 30-дневной летальности при острой ТЭЛА.\nПроще оригинальной шкалы PESI, включает всего 6 клинических переменных.',
}

tbsa_replacements = {
    '燒傷面積計算器，使用 Rule of Nines 和 Lund-Browder 圖表。\n是燒傷輸液計算(Parkland Formula)的前提工具。':
        'Калькулятор площади ожоговой поверхности (TBSA) по правилу девяток и таблице Лунда-Браудера.\nИспользуется для расчета инфузионной терапии при ожогах (формула Паркланда).',
    '使用 Rule of Nines 計算燒傷面積百分比。\n    成人與兒童有不同的體表面積分布。\n\n    輸出: TBSA %':
        'Расчет процента площади ожоговой поверхности по правилу девяток.\n    Анатомическое распределение площади тела отличается у взрослых и детей.\n\n    Результат: % TBSA',
}

triss_replacements = {
    '結合生理評分 (RTS) 和解剖評分 (ISS) 的創傷存活預測模型。\n是創傷照護品質評估的國際標準。':
        'Модель прогнозирования выживаемости при травме, объединяющая физиологическую оценку (RTS) и анатомическую (ISS).\nМеждународный стандарт оценки качества травматологической помощи.',
    '計算創傷患者的存活機率，結合：\n    - RTS (Revised Trauma Score) - 生理評估\n    - ISS (Injury Severity Score) - 解剖評估\n    - Age - 年齡修正\n    - Injury type - 鈍傷 vs 穿刺傷\n\n    輸出: 存活機率 Ps (0-100%)':
        'Расчет вероятности выживания пострадавших с травмой на основе:\n    - RTS (Revised Trauma Score) - физиологическая оценка\n    - ISS (Injury Severity Score) - анатомическая оценка\n    - Возраст (коррекция по возрасту)\n    - Характер травмы - тупая или проникающая\n\n    Результат: вероятность выживания Ps (0-100%)',
}

chads2_va_replacements = {
    '''    CHA₂DS₂-VA 計分系統（2024年ESC心房顫動指引）

    2024年ESC指引移除性別作為風險修飾因子，原因：
    - 單純女性性別在沒有其他因素下不增加中風風險
    - 避免基於性別的治療差異
    - 簡化臨床決策''':
    '''    CHA₂DS₂-VA шкала оценки риска инсульта (рекомендации ESC 2024 по фибрилляции предсердий)

    Рекомендации ESC 2024 исключили пол как модификатор риска:
    - Женский пол сам по себе без других факторов не увеличивает риск инсульта
    - Устранение различий в лечении по признаку пола
    - Упрощение принятия клинических решений''',

    '''                    "新版",
                    "心房顫動",
                    "抗凝血",''':
    '''                    "новая версия",
                    "фибрилляция предсердий",
                    "антикоагулянты",''',

    '''        計算CHA₂DS₂-VA分數（2024 ESC - 無性別因素版本）

        Args:
            chf_or_lvef_lte_40: CHF or LVEF ≤40% / 心衰竭或LVEF≤40%
            hypertension: History of hypertension / 高血壓病史
            age_gte_75: Age ≥75 years (2 points) / 年齡≥75歲（2分）
            diabetes: Diabetes mellitus / 糖尿病
            stroke_tia_or_te_history: Prior stroke, TIA, or thromboembolism (2 points) /
                                       中風/TIA/血栓栓塞病史（2分）
            vascular_disease: Prior MI, PAD, or aortic plaque /
                              心肌梗塞、周邊動脈疾病或主動脈斑塊
            age_65_to_74: Age 65-74 years (1 point; mutually exclusive with age ≥75) /
                          年齡65-74歲（1分；與≥75歲互斥）''':
    '''        Расчет шкалы CHA₂DS₂-VA (ESC 2024 - версия без учета пола)

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
                          Возраст 65-74 года (1 балл; взаимоисключающий с возрастом ≥75)''',

    '''            "C - CHF/LVEF ≤40% (心衰竭)": 1 if chf_or_lvef_lte_40 else 0,
            "H - Hypertension (高血壓)": 1 if hypertension else 0,
            "A₂ - Age ≥75 (年齡≥75歲)": 2 if age_gte_75 else 0,
            "D - Diabetes (糖尿病)": 1 if diabetes else 0,
            "S₂ - Stroke/TIA/TE (中風史)": 2 if stroke_tia_or_te_history else 0,
            "V - Vascular disease (血管疾病)": 1 if vascular_disease else 0,
            "A - Age 65-74 (年齡65-74歲)": 1 if (age_65_to_74 and not age_gte_75) else 0,''':
    '''            "C - CHF/LVEF ≤40% (ХСН/ФВЛЖ ≤40%)": 1 if chf_or_lvef_lte_40 else 0,
            "H - Hypertension (Артериальная гипертензия)": 1 if hypertension else 0,
            "A₂ - Age ≥75 (Возраст ≥75 лет)": 2 if age_gte_75 else 0,
            "D - Diabetes (Сахарный диабет)": 1 if diabetes else 0,
            "S₂ - Stroke/TIA/TE (Анамнез инсульта/ТИА/ТЭ)": 2 if stroke_tia_or_te_history else 0,
            "V - Vascular disease (Сосудистые заболевания)": 1 if vascular_disease else 0,
            "A - Age 65-74 (Возраст 65-74 года)": 1 if (age_65_to_74 and not age_gte_75) else 0,''',

    '''        根據2024 ESC指引產生CHA₂DS₂-VA分數解讀''':
    '''        Интерпретация балла CHA₂DS₂-VA согласно клиническим рекомендациям ESC 2024''',

    '''            detail_zh = f"根據2024 ESC指引為極低中風風險。年中風率約{annual_risk}。不建議抗凝血治療。"
            recommendations = [
                "No anticoagulation recommended (不建議抗凝血)",
                "Address modifiable cardiovascular risk factors",
                "Reassess risk factors periodically",
            ]
            next_steps = [
                "控制高血壓、糖尿病等可改變風險因子",
                "定期重新評估CHA₂DS₂-VA分數",
                "生活型態調整以降低心血管風險",
            ]''':
    '''            detail_zh = f"По рекомендациям ESC 2024 риск инсульта очень низкий. Годовой риск ~{annual_risk}. Антикоагуляция не рекомендуется."
            recommendations = [
                "No anticoagulation recommended (Антикоагуляция не рекомендуется)",
                "Address modifiable cardiovascular risk factors",
                "Reassess risk factors periodically",
            ]
            next_steps = [
                "Контроль модифицируемых факторов риска (АД, гликемия)",
                "Периодическая переоценка риска по шкале CHA₂DS₂-VA",
                "Коррекция образа жизни для снижения сердечно-сосудистого риска",
            ]''',

    '''            detail_zh = f"根據2024 ESC指引為低中風風險。年中風率約{annual_risk}。應依個別評估考慮抗凝血治療。"
            recommendations = [
                "Anticoagulation should be considered (應考慮抗凝血)",
                "Assess bleeding risk with HAS-BLED score",
                "Shared decision-making with patient",
                "DOACs preferred over VKA if OAC chosen",
            ]
            next_steps = [
                "計算HAS-BLED評估出血風險",
                "與病患共同決策討論利弊",
                "若決定抗凝血，DOAC為首選",
                "處理可改變的出血風險因子",
            ]''':
    '''            detail_zh = f"По рекомендациям ESC 2024 риск инсульта низкий. Годовой риск ~{annual_risk}. Следует рассмотреть прием антикоагулянтов индивидуально."
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
            ]''',

    '''            detail_zh = f"根據2024 ESC指引為{'中度' if score <= 3 else '高度'}中風風險。年中風率約{annual_risk}。建議口服抗凝血治療。"
            recommendations = [
                "Oral anticoagulation is recommended (建議口服抗凝血)",
                "DOACs preferred over VKA (except mechanical valves, moderate-severe MS)",
                "Aspirin monotherapy is NOT adequate for stroke prevention",
            ]
            next_steps = [
                "評估腎功能以決定DOAC劑量",
                "計算HAS-BLED辨識可改變的出血風險",
                "依病患因素選擇適當DOAC",
                "確保病患衛教理解抗凝血治療",
            ]

            if score >= 4:
                recommendations.append("High stroke risk - ensure OAC adherence (高風險-確保服藥順從性)")''':
    '''            detail_zh = f"По рекомендациям ESC 2024 риск инсульта {'умеренный' if score <= 3 else 'высокий'}. Годовой риск ~{annual_risk}. Рекомендуется прием пероральных антикоагулянтов."
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
                recommendations.append("High stroke risk - ensure OAC adherence (Высокий риск инсульта - обеспечить приверженность терапии)")''',

    '''            stage_description=f"Annual stroke risk: {annual_risk} | 年中風風險: {annual_risk}",''':
    '''            stage_description=f"Annual stroke risk: {annual_risk} | Годовой риск инсульта: {annual_risk}",''',

    '''            warnings=("High stroke risk - anticoagulation strongly recommended (高中風風險-強烈建議抗凝血)",) if score >= 4 else tuple(),''':
    '''            warnings=("High stroke risk - anticoagulation strongly recommended (Высокий риск инсульта - настоятельно рекомендуется антикоагуляция)",) if score >= 4 else tuple(),''',
}

files_map = {
    'servers/medical-calc-mcp/src/domain/services/calculators/aims65.py': aims65_replacements,
    'servers/medical-calc-mcp/src/domain/services/calculators/apgar_score.py': apgar_replacements,
    'servers/medical-calc-mcp/src/domain/services/calculators/euroscore_ii.py': euroscore_replacements,
    'servers/medical-calc-mcp/src/domain/services/calculators/glasgow_blatchford.py': glasgow_replacements,
    'servers/medical-calc-mcp/src/domain/services/calculators/iss.py': iss_replacements,
    'servers/medical-calc-mcp/src/domain/services/calculators/lille_model.py': lille_replacements,
    'servers/medical-calc-mcp/src/domain/services/calculators/maddrey_df.py': maddrey_replacements,
    'servers/medical-calc-mcp/src/domain/services/calculators/pediatric_sofa.py': pediatric_sofa_replacements,
    'servers/medical-calc-mcp/src/domain/services/calculators/rts.py': rts_replacements,
    'servers/medical-calc-mcp/src/domain/services/calculators/spesi.py': spesi_replacements,
    'servers/medical-calc-mcp/src/domain/services/calculators/tbsa.py': tbsa_replacements,
    'servers/medical-calc-mcp/src/domain/services/calculators/triss.py': triss_replacements,
    'servers/medical-calc-mcp/src/domain/services/calculators/chads2_va.py': chads2_va_replacements,
}

def main():
    print("=== Step 1: Replace Chinese text ===")
    for path, reps in files_map.items():
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        replaced = 0
        norm_content = content.replace('\r\n', '\n')
        for target, rep in reps.items():
            norm_target = target.replace('\r\n', '\n')
            if norm_target in norm_content:
                norm_content = norm_content.replace(norm_target, rep.replace('\r\n', '\n'))
                replaced += 1
            else:
                print(f"Warning: Target not found in {path}:\n{repr(target[:60])}...")
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(norm_content)
        print(f"File {path}: {replaced}/{len(reps)} replacements applied.")

    print("\n=== Step 2: Add educational header to all calculator files ===")
    all_files = glob.glob('servers/medical-calc-mcp/src/domain/services/calculators/*.py')
    header_check = "Медицинские калькуляры, используются для обучения технологиям MCP"
    
    header_added = 0
    for file_path in all_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        if header_check not in content:
            # Prepend header
            content = HEADER + content
            with open(file_path, 'w', encoding='utf-8', newline='\n') as f:
                f.write(content)
            header_added += 1

    print(f"Added header to {header_added} files (total files: {len(all_files)}).")

    print("\n=== Step 3: Check remaining Chinese characters in calculators ===")
    chinese_pattern = re.compile(r'[\u4e00-\u9fff]')
    remaining_chinese = []
    for file_path in all_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        matches = chinese_pattern.findall(content)
        if matches:
            remaining_chinese.append((file_path, len(matches)))

    if remaining_chinese:
        print(f"WARNING: Chinese characters still present in {len(remaining_chinese)} files:")
        for fp, count in remaining_chinese:
            print(f"  {fp}: {count} chars")
    else:
        print("SUCCESS: 0 Chinese characters found in all calculator files!")

if __name__ == '__main__':
    main()
