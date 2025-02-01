import streamlit as st
import pandas as pd
import requests
import json
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# GitHub credentials
GITHUB_USERNAME = os.getenv("BogdanBarnaMihai")
GITHUB_TOKEN = os.getenv("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")
GITHUB_REPO = os.getenv("gym-progress")
GITHUB_BRANCH = os.getenv("main")
WORKOUT_CSV_PATH = "workout_log.csv"  # File in GitHub repository

# Function to get the latest workout log file from GitHub
def get_github_file():
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/contents/{WORKOUT_CSV_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        file_data = response.json()
        return file_data["download_url"], file_data["sha"]
    return None, None

# Function to update workout_log.csv on GitHub
def update_github_csv(local_file):
    file_url, file_sha = get_github_file()
    if not file_url:
        st.error("Failed to fetch file from GitHub.")
        return
    
    # Read the local CSV file
    with open(local_file, "r") as file:
        content = file.read()
    
    # Prepare request payload
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/contents/{WORKOUT_CSV_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    payload = {
        "message": "Update workout log",
        "content": content.encode("utf-8").decode("utf-8"),
        "sha": file_sha,
        "branch": GITHUB_BRANCH
    }
    
    # Push update to GitHub
    response = requests.put(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        st.success("Workout log updated on GitHub!")
    else:
        st.error(f"Failed to update GitHub. {response.json()}")

# Initialize workout log locally
if not os.path.exists("workout_log.csv"):
    pd.DataFrame(columns=["Date", "Exercise", "Weight"]).to_csv("workout_log.csv", index=False)

# Streamlit UI
st.title("Gym Progress Tracker")

# Workout input fields
st.header("Add Workout Record")
exercises = [
    "Incline Smith Machine Bench Press", "Machine Pec Fly", "Smith Machine Shoulder Press",
    "Machine Lat Row", "Machine Upper Back Row", "Pulldown", "Carter Extensions",
    "Preacher Curls", "Machine Lateral Raise", "S/A Standing Rear Delt Fly", "Squats",
    "Lying Hamstring Curl", "Standing Hamstring Curl", "Abductors Machine", "Leg Extensions",
    "Calf Raises", "Standing Traps Shrugs"
]
selected_exercise = st.selectbox("Select Exercise", exercises)
input_weight = st.number_input("Enter Weight", min_value=0.0, step=0.5)

# Add workout button
if st.button("Add Record"):
    if selected_exercise and input_weight > 0:
        new_record = {
            "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Exercise": selected_exercise,
            "Weight": input_weight
        }
        
        # Save locally
        df = pd.read_csv("workout_log.csv")
        df = df.append(new_record, ignore_index=True)
        df.to_csv("workout_log.csv", index=False)
        
        # Push update to GitHub
        update_github_csv("workout_log.csv")
    else:
        st.error("Please enter a valid weight.")

# Display existing records
st.header("Workout History")
if os.path.exists("workout_log.csv"):
    df = pd.read_csv("workout_log.csv")
    st.dataframe(df)
else:
    st.write("No records found.")
