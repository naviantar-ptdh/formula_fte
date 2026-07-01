import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import pearsonr
from sklearn.linear_model import LinearRegression
import plotly.express as px

st.set_page_config(
    page_title="FTE Correlation Test",
    layout="wide"
)

st.title("FTE Formula Consistency Test")

# ==========================================
# INPUT SAMPLE
# ==========================================

n_sample = st.number_input(
    "Number of Samples",
    min_value=5,
    value=66,
    step=1
)

# ==========================================
# DEFAULT VARIABLES
# ==========================================

st.subheader("Default FTE Variables")

default_data = {
    "Variable": [
        "Breakdown Time",
        "Load Factor",
        "Competency Factor",
        "EMHD",
        "Manpower Factor"
    ],
    "Default Value": [
        3.6,
        3,
        0.80,
        7.9,
        1.44
    ]
}

default_df = pd.DataFrame(default_data)

edited_df = st.data_editor(
    default_df,
    use_container_width=True,
    num_rows="fixed"
)

# ==========================================
# VARIABLE TEST
# ==========================================

test_variable = st.selectbox(
    "Select Variable to Test",
    edited_df["Variable"]
)

st.subheader("Paste Data")

input_text = st.text_area(
    "Paste values here (one value per line)",
    height=250,
    placeholder="""2.5
3.1
4.0
5.2"""
)

# ==========================================
# CALCULATE
# ==========================================

if st.button("Run Correlation"):

    try:

        values = [
            float(x)
            for x in input_text.strip().splitlines()
            if x.strip()
        ]

        if len(values) != n_sample:
            st.error(
                f"Number of data ({len(values)}) "
                f"does not match sample size ({n_sample})"
            )
            st.stop()

        df = pd.DataFrame({
            test_variable: values
        })

        defaults = dict(
            zip(
                edited_df["Variable"],
                edited_df["Default Value"]
            )
        )

        breakdown = defaults["Breakdown Time"]
        load_factor = defaults["Load Factor"]
        competency = defaults["Competency Factor"]
        emhd = defaults["EMHD"]
        manpower = defaults["Manpower Factor"]

        # Replace selected variable
        if test_variable == "Breakdown Time":
            breakdown = np.array(values)

        elif test_variable == "Load Factor":
            load_factor = np.array(values)

        elif test_variable == "Competency Factor":
            competency = np.array(values)

        elif test_variable == "EMHD":
            emhd = np.array(values)

        elif test_variable == "Manpower Factor":
            manpower = np.array(values)

        # ==================================
        # FTE FORMULA
        # ==================================

        fte = (
            (breakdown / emhd)
            * load_factor
            / competency
            * manpower
        )

        df["FTE"] = fte

        # ==================================
        # CORRELATION
        # ==================================

        r, p = pearsonr(
            df[test_variable],
            df["FTE"]
        )

        # ==================================
        # REGRESSION
        # ==================================

        X = df[[test_variable]]
        y = df["FTE"]

        model = LinearRegression()
        model.fit(X, y)

        slope = model.coef_[0]
        intercept = model.intercept_

        r2 = model.score(X, y)

        st.success("Analysis Complete")

        col1, col2, col3 = st.columns(3)

        col1.metric("Correlation (r)", round(r, 4))
        col2.metric("P-Value", round(p, 6))
        col3.metric("R²", round(r2, 4))

        st.markdown(
            f"""
            ### Regression Equation

            **FTE = {intercept:.4f} + ({slope:.4f} × {test_variable})**
            """
        )

        # ==================================
        # SCATTER PLOT
        # ==================================

        fig = px.scatter(
            df,
            x=test_variable,
            y="FTE",
            trendline="ols",
            title=f"{test_variable} vs FTE"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        st.subheader("Result Data")

        st.dataframe(
            df,
            use_container_width=True
        )

    except Exception as e:
        st.error(str(e))