"""Streamlit-демо: формы строятся из каталога MCP, расчёт идёт через stdio."""

import streamlit as st

from mcp_calc.client import call_tool_sync, fetch_demo_state_sync
from mcp_calc.models import DISCLAIMER

st.set_page_config(page_title="Медицинские калькуляторы", page_icon="∑", layout="wide")
st.markdown(
    """
    <style>
    .block-container {padding-top: 1.4rem; max-width: 1080px;}
    div[data-testid="stMetricValue"] {font-size: 2rem;}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner="Подключение к MCP-серверу...")
def load_demo_state() -> dict:
    state = fetch_demo_state_sync()
    if any("methodology" not in item for item in state["calculators"]):
        raise RuntimeError("Сервер не прислал методику расчёта.")
    return state


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


try:
    state = load_demo_state()
except Exception as exc:
    st.error("Не удалось подключиться к MCP-серверу.")
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
    if st.button("Переподключить"):
        load_demo_state.clear()
        st.rerun()
    st.divider()
    st.caption("Транспорт: stdio. Tools, которые сервер отдал по MCP:")
    st.markdown("\n".join(f"- `{name}`" for name in state["tool_names"]))
    st.divider()
    st.caption(DISCLAIMER)

selected = by_id[selected_id]
st.title("Медицинские калькуляторы")
st.caption("Демонстрация MCP. Форма собрана из `list_calculators`, расчёт вызывает tool сервера.")
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
