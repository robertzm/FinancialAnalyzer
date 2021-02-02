"""Prepare data for Plotly Dash."""
import pandas as pd
from app import db


def create_dataframe():
    """Create Pandas DataFrame from local CSV."""
    df = pd.read_sql("SELECT * from TransRecord", db.get_engine(), parse_dates=["timeslot", "date"])
    df["timeslot"] = df["timeslot"].dt.date
    df.drop(columns=["uuid", "date", "description", "uploadfile"], inplace=True)
    return df[df['gain'] == 0]
