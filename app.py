import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(page_title="CBSE Class XII Result Analytics", page_icon="📊", layout="wide")

st.title("📊 CBSE Class XII Commerce Result Analytics Dashboard")
st.caption("A student project using Python, Pandas, Plotly and Streamlit")
st.info("This project uses fictional sample data for demonstration. The support indicator is only an example and is not an official CBSE pass/fail decision.")

REQUIRED_COLUMNS = ["Student_ID", "Student_Name", "Section", "English", "Accountancy",
                    "Business_Studies", "Economics", "Informatics_Practices"]
SUBJECTS = ["English", "Accountancy", "Business_Studies", "Economics", "Informatics_Practices"]

def prepare_data(df):
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError("Missing required column(s): " + ", ".join(missing))
    df = df.copy()
    for subject in SUBJECTS:
        df[subject] = pd.to_numeric(df[subject], errors="coerce")
    if df[SUBJECTS].isna().any().any():
        raise ValueError("Some subject marks are blank or non-numeric. Please correct the CSV.")
    for subject in SUBJECTS:
        if ((df[subject] < 0) | (df[subject] > 100)).any():
            raise ValueError(f"Marks in {subject} must be between 0 and 100.")
    df["Total"] = df[SUBJECTS].sum(axis=1)
    df["Percentage"] = (df["Total"] / (len(SUBJECTS) * 100) * 100).round(2)
    df["Average_Mark"] = df[SUBJECTS].mean(axis=1).round(2)
    # Demonstration-only flag; school rules may differ.
    df["Needs_Support"] = df[SUBJECTS].lt(40).any(axis=1)
    return df

default_path = Path(__file__).parent / "data" / "sample_results.csv"
uploaded = st.sidebar.file_uploader("Upload a results CSV", type=["csv"])
try:
    raw = pd.read_csv(uploaded) if uploaded is not None else pd.read_csv(default_path)
    data = prepare_data(raw)
except Exception as exc:
    st.error(f"Could not load the dataset: {exc}")
    st.stop()

st.sidebar.header("Filters")
sections = ["All"] + sorted(data["Section"].dropna().astype(str).unique().tolist())
chosen_section = st.sidebar.selectbox("Choose section", sections)
if chosen_section != "All":
    data = data[data["Section"].astype(str) == chosen_section]

if data.empty:
    st.warning("No records match this filter.")
    st.stop()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Students", int(data["Student_ID"].nunique()))
c2.metric("Class average", f"{data['Percentage'].mean():.1f}%")
c3.metric("Highest percentage", f"{data['Percentage'].max():.1f}%")
c4.metric("Students flagged for support", int(data["Needs_Support"].sum()))

st.subheader("Student-wise results")
display_cols = ["Student_ID", "Student_Name", "Section"] + SUBJECTS + ["Total", "Percentage", "Needs_Support"]
st.dataframe(data[display_cols].sort_values("Percentage", ascending=False), use_container_width=True)

left, right = st.columns(2)
with left:
    st.subheader("Average mark by subject")
    subject_avg = data[SUBJECTS].mean().rename_axis("Subject").reset_index(name="Average_Mark")
    subject_avg["Subject"] = subject_avg["Subject"].str.replace("_", " ")
    fig = px.bar(subject_avg, x="Subject", y="Average_Mark", range_y=[0, 100],
                 title="Class average in each subject", text_auto=".1f")
    st.plotly_chart(fig, use_container_width=True)
with right:
    st.subheader("Percentage distribution")
    fig2 = px.histogram(data, x="Percentage", nbins=10, title="How student percentages are distributed")
    st.plotly_chart(fig2, use_container_width=True)

st.subheader("Students who may need additional support")
support = data[data["Needs_Support"]]
if support.empty:
    st.success("No students are flagged by this demonstration rule in the selected data.")
else:
    st.dataframe(support[["Student_ID", "Student_Name", "Section"] + SUBJECTS],
                 use_container_width=True)

csv = data[display_cols].to_csv(index=False).encode("utf-8")
st.download_button("Download filtered analysis as CSV", csv, "result_analysis.csv", "text/csv")

st.markdown("---")
st.caption("Privacy note: use anonymised IDs for real student data and obtain permission before processing or sharing marks.")
