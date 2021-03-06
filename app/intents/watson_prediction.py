import pandas as pd
import streamlit as st
from app.helper_functions import read_df, download_link
from src.intents.watson_prediction import eval_intent_col, run_wa_preds, cache_df
from src.helper_functions import setup_logger

logger = setup_logger()

def watson_prediction_page(state):
    logger.info({"message": "Loading Watson Prediction page."})
    st.title("Watson Prediction")

    st.markdown("""
    In this page you can upload a file with examples to be evaluated by your Watson Assistant skill.

    # How can this help me?

    If you are creating new intents, it's important to check what predictions your Watson Assistant provide for these examples.

    You can avoid possible conflicts with old intents in the model.
    """)

    st.markdown("## Import file")
    st.markdown("""
    File format

    | example | intents (optional) |
    | - | - |
    | I want an order status | #check_order |
    | How to check my order? | #check_order |
    | I want to order | #place_order |

    Without column name!
    """)
    # UPLOAD FILE
    uploaded_file = st.file_uploader(
        "Attach file", type=["csv", "xlsx"])
    if uploaded_file is not None:
        data = read_df(uploaded_file, cols_names=["examples", "intents"])
        data = eval_intent_col(data)
        if state.watson_prediction is None:
            state.watson_prediction = data.copy()
    else:
        state.watson_prediction = None

    # RUN ANALYSIS
    if isinstance(state.watson_prediction, pd.DataFrame):
        if len(state.watson_prediction) >= 500:
            warning_msg = "Caution! This analysis will make several API calls and will incur costs. It will make {} API calls.".format(
                len(state.watson_prediction["examples"].tolist()))
            logger.warning({"message": warning_msg})
            st.warning(warning_msg)

        if st.button("Run Analysis"):
            if "watson_intent_0" not in state.watson_prediction.columns:
                st.write("Getting Watson predictions.")

            data_processed = run_wa_preds(df=state.watson_prediction,
                                          watson_apikey=state.watson_args["apikey"],
                                          watson_endpoint=state.watson_args["endpoint"],
                                          watson_skill=state.watson_args["skill_id"])

            state.watson_prediction = cache_df(data_processed.copy())

    # SHOW DATASET
    if isinstance(state.watson_prediction, pd.DataFrame):
        if "watson_intent_0" in state.watson_prediction.columns:
            st.subheader("Watson Predictions")

            data = state.watson_prediction.copy()

            filters = {}
            if "intents" in data.columns:
                filters["intents"] = st.multiselect(label="Filter intents",
                                                    options=data["intents"].unique(
                                                    ).tolist(),
                                                    default=data["intents"].unique().tolist())
            else:
                filters["intents"] = None

            filters["wa_intents"] = st.multiselect(label="Filter Watson intents",
                                                   options=data["watson_intent_0"].unique(
                                                   ).tolist(),
                                                   default=data["watson_intent_0"].unique().tolist())

            filters["wa_conf"] = st.slider('Watson confidence (0)', min_value=0.0,
                                           max_value=1.0, value=(0.6, 1.0), step=0.01)

            if filters["intents"] is not None:
                data = data[(data["watson_confidence_0"] >= filters["wa_conf"][0]) &
                            (data["watson_confidence_0"] <= filters["wa_conf"][1]) &
                            (data["watson_intent_0"].isin(filters["wa_intents"])) &
                            (data["intents"].isin(filters["intents"]))]
            else:
                data = data[(data["watson_confidence_0"] >= filters["wa_conf"][0]) &
                            (data["watson_confidence_0"] <= filters["wa_conf"][1]) &
                            (data["watson_intent_0"].isin(filters["wa_intents"]))]

            # filters (intents, watson_intents_0, watson_confidence_0)

            st.write("Rows selected: {}".format(len(data)))

            link = download_link(
                data, "watson_prediction.csv", "Download CSV file")
            st.markdown(link, unsafe_allow_html=True)

            st.write(data)

    state.sync()
