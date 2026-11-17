"""Streamlit-демо: формы строятся из каталога MCP, расчёт идёт через stdio и сетевой SSE."""

import streamlit as st

from mcp_calc.client import call_tool_sync, fetch_demo_state_sync
from mcp_calc.external_client import call_external_tool_sync, fetch_external_tools_sync
from mcp_calc.models import DISCLAIMER
from mcp_calc.network_client import (
    calculate_network_sync,
    discover_calculators_sync,
    get_calculator_schema_sync,
)
from mcp_calc.translations import (
    get_tool_keywords,
    translate_any_text,
    translate_component_label,
    translate_param_name,
    translate_recommendations,
    translate_severity,
    translate_specialty,
    translate_summary,
    translate_tool_name,
    translate_tool_purpose,
    translate_unit,
)

st.set_page_config(page_title="Медицинские калькуляторы и MCP", page_icon="🩺", layout="wide")
st.markdown(
    """
    <style>
    .block-container {padding-top: 1.4rem; max-width: 1160px;}
    div[data-testid="stMetricValue"] {font-size: 2rem;}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner="Подключение к локальному MCP-серверу...")
def load_demo_state() -> dict:
    state = fetch_demo_state_sync()
    if any("methodology" not in item for item in state["calculators"]):
        raise RuntimeError("Сервер не прислал методику расчёта.")
    return state


@st.cache_data(show_spinner="Подключение к внешнему medical-mcp серверу...")
def load_external_tools_state() -> list[dict]:
    return fetch_external_tools_sync()


@st.cache_data(show_spinner="Получение списка калькуляторов с сетевого сервера (порт 8000)...")
def load_network_calculators_state() -> list[dict]:
    res = discover_calculators_sync(by="tools", limit=250)
    raw_tools = res.get("tools", [])
    enriched = []
    for t in raw_tools:
        tid = t["tool_id"]
        ru_name = translate_tool_name(tid, t.get("name", tid))
        ru_purpose = translate_tool_purpose(tid, t.get("purpose", ""))
        keywords = get_tool_keywords(tid)
        specialties = [translate_specialty(s) for s in t.get("specialties", [])] + t.get("specialties", [])

        search_corpus = " ".join([
            tid,
            t.get("name", ""),
            ru_name,
            t.get("purpose", ""),
            ru_purpose,
            " ".join(keywords),
            " ".join(specialties),
        ]).lower()

        item = dict(t)
        item["ru_name"] = ru_name
        item["ru_purpose"] = ru_purpose
        item["search_corpus"] = search_corpus
        enriched.append(item)
    return enriched


@st.cache_data(show_spinner="Загрузка схемы калькулятора...")
def load_network_schema_state(tool_id: str) -> dict:
    return get_calculator_schema_sync(tool_id)


def friendly_tool_error(message: str) -> str:
    marker = ": "
    prefix = "Error executing tool "
    if message.startswith(prefix) and marker in message:
        return message.split(marker, 1)[1]
    return message


def render_input(calculator_id: str, spec: dict):
    label = spec["label"]
    if spec.get("unit"):
        label = f"{label}, {spec['unit']}"
    help_text = spec.get("help")
    key = f"{calculator_id}-{spec['name']}"
    kind = spec["type"]
    if kind == "boolean":
        return st.checkbox(label, value=bool(spec.get("default", False)), help=help_text, key=key)
    if kind == "enum":
        options = spec["options"]
        labels = [item["label"] for item in options]
        default = spec.get("default")
        index = next((i for i, item in enumerate(options) if item["value"] == default), 0)
        selected = st.selectbox(label, options=labels, index=index, help=help_text, key=key)
        return options[labels.index(selected)]["value"]
    if kind == "integer":
        return int(
            st.number_input(
                label,
                min_value=int(spec["minimum"]),
                max_value=int(spec["maximum"]),
                value=int(spec["default"]),
                step=int(spec.get("step") or 1),
                help=help_text,
                key=key,
            )
        )
    return float(
        st.number_input(
            label,
            min_value=float(spec["minimum"]),
            max_value=float(spec["maximum"]),
            value=float(spec["default"]),
            step=float(spec.get("step") or 0.1),
            help=help_text,
            key=key,
        )
    )


def render_result(result: dict) -> None:
    with st.container(border=True):
        st.metric(result["name"], f"{result['value_display']} {result['unit']}")
        st.write(result["interpretation"])
        if result.get("components"):
            st.dataframe(
                [{"Показатель": item["label"], "Значение": item["value"]} for item in result["components"]],
                hide_index=True,
                use_container_width=True,
            )
        st.caption(result["formula"])
        st.caption(result["reference"])
    st.caption(result["disclaimer"])


EXTERNAL_TOOL_TITLES = {
    "search-drugs": "Поиск лекарств в базе FDA",
    "get-drug-details": "Детали препарата по коду NDC",
    "get-health-statistics": "Статистика ВОЗ (WHO Global Observatory)",
    "search-medical-literature": "Поиск исследований в PubMed",
    "get-article-details": "Детали статьи по PubMed ID (PMID)",
    "search-drug-nomenclature": "Стандартизированные названия RxNorm",
    "search-google-scholar": "Поиск статей в Google Scholar",
    "search-clinical-guidelines": "Клинические рекомендации",
    "search-medical-databases": "Комплексный поиск по медбазам",
    "search-medical-journals": "Поиск по топ-журналам (NEJM, Lancet, JAMA)",
}

# --- Сайдбар: выбор сервера ---
with st.sidebar:
    st.subheader("MCP Сервер")
    server_mode = st.radio(
        "Выберите сервер:",
        [
            "Локальный (Калькуляторы)",
            "Внешний (medical-mcp)",
            "Сетевой (medical-calc-mcp, порт 8000)",
        ],
        label_visibility="collapsed",
    )
    if st.button("Переподключить", use_container_width=True):
        load_demo_state.clear()
        load_external_tools_state.clear()
        load_network_calculators_state.clear()
        load_network_schema_state.clear()
        st.rerun()

    st.divider()

# ========================================================
# РЕЖИМ 1: Локальные учебные калькуляторы
# ========================================================
if server_mode == "Локальный (Калькуляторы)":
    try:
        state = load_demo_state()
    except Exception as exc:
        st.error("Не удалось подключиться к локальному MCP-серверу.")
        st.exception(exc)
        st.stop()

    calculators = state["calculators"]
    by_id = {item["id"]: item for item in calculators}

    with st.sidebar:
        st.header("Калькуляторы")
        selected_id = st.radio(
            "Калькулятор",
            list(by_id),
            format_func=lambda calculator_id: by_id[calculator_id]["name"],
            label_visibility="collapsed",
        )
        st.divider()
        st.caption("Транспорт: stdio. Tools локального сервера:")
        st.markdown("\n".join(f"- `{name}`" for name in state["tool_names"]))
        st.divider()
        st.caption(DISCLAIMER)

    selected = by_id[selected_id]
    st.title("Медицинские калькуляторы")
    st.caption("Локальный MCP-сервер `mcp_calc.server`. Форма собрана из `list_calculators`.")
    st.subheader(selected["name"])
    st.write(selected["summary"])
    st.code(selected["id"], language=None)
    with st.expander("Методика расчёта"):
        st.markdown(selected["methodology"])

    form_column, result_column = st.columns(2, gap="large")
    with form_column:
        with st.form(f"form-{selected_id}"):
            arguments = {spec["name"]: render_input(selected_id, spec) for spec in selected["inputs"]}
            submitted = st.form_submit_button("Рассчитать", type="primary", use_container_width=True)

    with result_column:
        if not submitted:
            st.info("Нажмите «Рассчитать». Запрос уйдёт в MCP-сервер отдельным процессом.")
        else:
            error_message = None
            try:
                with st.spinner("Считаю через MCP..."):
                    result = call_tool_sync(selected_id, arguments)
            except Exception as exc:
                error_message = friendly_tool_error(str(exc))
                st.error(error_message)
                result = None
            if result is not None:
                render_result(result)
            with st.expander("Запрос и ответ MCP"):
                st.json(
                    {
                        "tool": selected_id,
                        "arguments": arguments,
                        "result": result if error_message is None else error_message,
                    }
                )

# ========================================================
# РЕЖИМ 2: Внешний сервер medical-mcp
# ========================================================
elif server_mode == "Внешний (medical-mcp)":
    try:
        external_tools = load_external_tools_state()
    except Exception as exc:
        st.error("Не удалось подключиться к внешнему MCP-серверу `medical-mcp`.")
        st.exception(exc)
        st.stop()

    ext_by_name = {t["name"]: t for t in external_tools}

    with st.sidebar:
        st.header("Внешние инструменты")
        selected_tool_name = st.radio(
            "Инструмент",
            list(ext_by_name),
            format_func=lambda name: EXTERNAL_TOOL_TITLES.get(name, name),
            label_visibility="collapsed",
        )
        st.divider()
        st.caption("Транспорт: stdio (`medical-mcp`).")
        st.caption("Источники: FDA, WHO, PubMed, RxNorm, Google Scholar.")

    current_tool = ext_by_name[selected_tool_name]
    st.title("Внешний MCP: Медицинские базы данных")
    st.caption("Подключение к внешнему серверу `medical-mcp` (FDA, PubMed, WHO, RxNorm).")

    display_title = EXTERNAL_TOOL_TITLES.get(selected_tool_name, selected_tool_name)
    st.subheader(f"{display_title} (`{selected_tool_name}`)")
    st.write(current_tool["description"])

    schema = current_tool.get("input_schema", {})
    props = schema.get("properties", {})
    required_props = set(schema.get("required", []))

    form_col, res_col = st.columns(2, gap="large")

    with form_col:
        with st.form(f"ext-form-{selected_tool_name}"):
            ext_args = {}
            for p_name, p_spec in props.items():
                p_type = p_spec.get("type", "string")
                p_desc = p_spec.get("description", p_name)
                req_marker = " *" if p_name in required_props else ""
                label = f"{p_name}{req_marker}: {p_desc}"
                key = f"ext-{selected_tool_name}-{p_name}"

                if p_type == "integer":
                    min_val = p_spec.get("minimum", 1)
                    max_val = p_spec.get("maximum", 100)
                    default_val = p_spec.get("default", min_val)
                    ext_args[p_name] = int(
                        st.number_input(label, min_value=min_val, max_value=max_val, value=default_val, key=key)
                    )
                else:
                    default_str = p_spec.get("default", "")
                    placeholder = ""
                    if p_name == "query":
                        placeholder = "например: aspirin, hypertension, covid-19"
                    elif p_name == "ndc":
                        placeholder = "например: 0006-0031-28"
                    elif p_name == "pmid":
                        placeholder = "например: 31881180"
                    elif p_name == "indicator":
                        placeholder = "например: Life expectancy"
                    ext_args[p_name] = st.text_input(
                        label,
                        value=default_str,
                        placeholder=placeholder,
                        key=key,
                    )

            ext_submitted = st.form_submit_button("Выполнить через MCP", type="primary", use_container_width=True)

    with res_col:
        if not ext_submitted:
            st.info("Заполните параметры и нажмите «Выполнить через MCP». Запрос будет передан во внешний MCP-сервер.")
        else:
            filtered_args = {k: v for k, v in ext_args.items() if v != "" or k in required_props}
            with st.spinner("Запрос во внешний MCP-сервер..."):
                try:
                    tool_output = call_external_tool_sync(selected_tool_name, filtered_args)
                    with st.container(border=True):
                        st.markdown(tool_output)
                    with st.expander("Сырой ответ MCP"):
                        st.json({
                            "server": "medical-mcp",
                            "tool": selected_tool_name,
                            "arguments": filtered_args,
                            "raw_text": tool_output,
                        })
                except Exception as exc:
                    st.error(f"Ошибка вызова MCP-инструмента: {exc}")
                    with st.expander("Детали ошибки"):
                        st.json({
                            "server": "medical-mcp",
                            "tool": selected_tool_name,
                            "arguments": filtered_args,
                            "error": str(exc),
                        })

# ========================================================
# РЕЖИМ 3: Сетевой сервер medical-calc-mcp (152 калькулятора, SSE :8000)
# ========================================================
else:
    try:
        network_tools = load_network_calculators_state()
    except Exception as exc:
        st.error("Не удалось подключиться к сетевому MCP-серверу на `http://127.0.0.1:8000/sse`.")
        st.info("Убедитесь, что сервер запущен: `scripts\\start_network_server.bat`")
        st.exception(exc)
        st.stop()

    with st.sidebar:
        st.header("152 Калькулятора")
        search_query = st.text_input("🔍 Поиск калькулятора:", placeholder="ckd, curb, sofa, gcs, инфаркт, инфекция, печень...").strip().lower()

        if search_query:
            words = search_query.split()
            filtered_tools = [
                t for t in network_tools
                if all(w in t.get("search_corpus", "") for w in words)
            ]
            if not filtered_tools:
                # Попробуем поиск по ключевому слову через MCP discover
                try:
                    disc_res = discover_calculators_sync(by="keyword", value=search_query, limit=50)
                    disc_tools = disc_res.get("tools", [])
                    if disc_tools:
                        disc_ids = {d["tool_id"] for d in disc_tools}
                        filtered_tools = [t for t in network_tools if t["tool_id"] in disc_ids]
                except Exception:
                    pass

            if not filtered_tools:
                st.warning(f"По запросу «{search_query}» ничего не найдено. Показан полный список.")
                filtered_tools = network_tools
        else:
            filtered_tools = network_tools

        tool_map = {t["tool_id"]: t for t in filtered_tools}
        count_label = f"Найдено: {len(filtered_tools)}" if search_query else f"Всего калькуляторов: {len(filtered_tools)}"
        selected_tool_id = st.selectbox(
            count_label,
            list(tool_map),
            format_func=lambda tid: f"{tool_map[tid].get('ru_name', translate_tool_name(tid, tool_map[tid].get('name', tid)))} ({tid})",
        )

        st.divider()
        st.caption("Транспорт: SSE по локальной сети (`http://127.0.0.1:8000/sse`).")
        st.caption("Архитектура: DDD Onion + FastMCP (152 формулы с доказательной базой PubMed).")

    # Загружаем схему выбранного калькулятора
    schema_info = load_network_schema_state(selected_tool_id)
    tool_meta = tool_map[selected_tool_id]
    russian_title = tool_meta.get("ru_name") or translate_tool_name(selected_tool_id, tool_meta["name"])
    russian_purpose = tool_meta.get("ru_purpose") or translate_tool_purpose(selected_tool_id, tool_meta.get("purpose", ""))

    st.title("Сетевой MCP: Клинические калькуляторы")
    st.caption("Сетевой сервер `medical-calc-mcp` (SSE на порту 8000). 152 калькулятора с доказательной базой PubMed.")

    st.subheader(f"{russian_title} (`{selected_tool_id}`)")
    st.write(russian_purpose)

    # Клинические области (специальности)
    context = schema_info.get("clinical_context", {})
    if context.get("specialties"):
        st.markdown(
            "**Клинические области:** " + ", ".join(f"`{translate_specialty(s)}`" for s in context["specialties"])
        )

    param_schemas = schema_info.get("param_schemas", {})
    required_params = set(schema_info.get("required_params", []))

    form_col, res_col = st.columns(2, gap="large")

    with form_col:
        with st.form(f"net-form-{selected_tool_id}"):
            calc_args = {}
            for p_name, p_info in param_schemas.items():
                p_desc = p_info.get("description", p_name)
                p_unit = p_info.get("unit", "")
                p_type = p_info.get("type", "number")

                translated_name = translate_param_name(p_name, p_desc)
                translated_unit = translate_unit(p_unit)
                unit_label = f" ({translated_unit})" if translated_unit else ""
                req_marker = " *" if p_name in required_params else ""
                label = f"{translated_name}{unit_label}{req_marker}"
                key = f"net-{selected_tool_id}-{p_name}"

                p_hint = p_info.get("clinical_hint", "")
                help_text = translate_any_text(p_hint) if p_hint and p_hint != "See calculator documentation" else None

                normal_range = p_info.get("normal_range")

                # Распознаём пол
                if p_name in ("gender", "sex"):
                    gender_labels = {"male": "Мужской (male)", "female": "Женский (female)"}
                    calc_args[p_name] = st.selectbox(
                        label,
                        options=["male", "female"],
                        format_func=lambda x: gender_labels.get(x, x),
                        help=help_text,
                        key=key,
                    )
                # Распознаём бинарные / булевы флаги (0 или 1)
                elif normal_range == [0, 1] or p_type == "boolean" or p_name.startswith(("is_", "has_", "confusion", "sbp_lt_", "age_gte_")):
                    checked = st.checkbox(label, value=False, help=help_text, key=key)
                    calc_args[p_name] = 1 if checked else 0
                # Числовые поля
                else:
                    min_val = float(normal_range[0]) if normal_range and len(normal_range) >= 2 else 0.0
                    max_val = float(normal_range[1]) if normal_range and len(normal_range) >= 2 else 500.0
                    if max_val <= min_val:
                        max_val = min_val + 100.0

                    default_val = min_val
                    if "age" in p_name:
                        default_val = 50.0
                    elif "creatinine" in p_name:
                        default_val = 1.0
                    elif min_val <= 1.0 <= max_val:
                        default_val = 1.0

                    step_val = 1.0 if "age" in p_name or "year" in p_unit or "heart_rate" in p_name else 0.1
                    calc_args[p_name] = st.number_input(
                        label,
                        min_value=min_val,
                        max_value=max_val,
                        value=float(default_val),
                        step=step_val,
                        help=help_text,
                        key=key,
                    )

            net_submitted = st.form_submit_button("Рассчитать через сетевой MCP", type="primary", use_container_width=True)

    with res_col:
        if not net_submitted:
            st.info("Заполните параметры и нажмите «Рассчитать через сетевой MCP». Запрос будет передан по протоколу SSE на `http://127.0.0.1:8000/sse`.")
        else:
            with st.spinner("Выполняю расчёт через сетевой MCP..."):
                try:
                    calc_response = calculate_network_sync(selected_tool_id, calc_args)
                    if not calc_response.get("success", True):
                        st.error(calc_response.get("error", "Ошибка расчёта."))
                    else:
                        with st.container(border=True):
                            score_val = calc_response.get("result")
                            score_unit = translate_unit(calc_response.get("unit", ""))
                            st.metric(russian_title, f"{score_val} {score_unit}")

                            interp = calc_response.get("interpretation", {})
                            if isinstance(interp, dict):
                                summary = interp.get("summary")
                                severity = interp.get("severity", "info")
                                severity_badge = translate_severity(severity)
                                if severity_badge:
                                    st.markdown(f"**Категория риска:** {severity_badge}")
                                if summary:
                                    rus_summary = translate_summary(summary)
                                    if severity in ("high", "severe"):
                                        st.error(rus_summary)
                                    elif severity in ("moderate", "mild"):
                                        st.warning(rus_summary)
                                    else:
                                        st.success(rus_summary)

                                rec = interp.get("recommendation")
                                if rec:
                                    st.markdown("**Клинические рекомендации:**")
                                    recs_list = translate_recommendations(rec)
                                    for r in recs_list:
                                        st.markdown(f"- {r}")

                            components = calc_response.get("component_scores")
                            if components and isinstance(components, dict):
                                st.markdown("**Составляющие шкалы:**")
                                st.dataframe(
                                    [{"Показатель": translate_component_label(k), "Значение": translate_component_label(str(v))}
                                     for k, v in components.items() if not k.startswith("_")],
                                    hide_index=True,
                                    use_container_width=True,
                                )

                            refs = calc_response.get("references", [])
                            if refs:
                                st.markdown("**Доказательная база и публикации (PubMed):**")
                                for r in refs:
                                    cit = r.get("citation", "")
                                    pmid = r.get("pmid")
                                    pmid_link = f" [PMID: {pmid}](https://pubmed.ncbi.nlm.nih.gov/{pmid}/)" if pmid else ""
                                    st.caption(f"• {cit}{pmid_link}")

                    with st.expander("Сетевой обмен MCP (JSON)"):
                        st.json({
                            "endpoint": "http://127.0.0.1:8000/sse",
                            "tool": selected_tool_id,
                            "arguments": calc_args,
                            "response": calc_response,
                        })
                except Exception as exc:
                    st.error(f"Ошибка вызова сетевого MCP: {exc}")
                    with st.expander("Детали ошибки"):
                        st.json({
                            "tool": selected_tool_id,
                            "arguments": calc_args,
                            "error": str(exc),
                        })
