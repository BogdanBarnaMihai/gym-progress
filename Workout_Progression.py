import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os
import matplotlib.pyplot as plt
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Paths to store the user credentials and workout records files
USER_DB_FILE = "user_db.json"
WORKOUT_RECORDS_FILE = "workout_records.json"

# GitHub Credentials from .env
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")
GITHUB_BRANCH = os.getenv("GITHUB_BRANCH")

# Load the user database from a JSON file
def load_user_db():
    if os.path.exists(USER_DB_FILE):
        with open(USER_DB_FILE, "r") as f:
            return json.load(f)
    return {}

# Save the user database to a JSON file
def save_user_db(user_db):
    with open(USER_DB_FILE, "w") as f:
        json.dump(user_db, f)

# Load workout records from a JSON file
def load_workout_records():
    if os.path.exists(WORKOUT_RECORDS_FILE):
        with open(WORKOUT_RECORDS_FILE, "r") as f:
            data = json.load(f)
            return pd.DataFrame(data) if data else pd.DataFrame(columns=["id", "date", "exercise", "weight"])
    return pd.DataFrame(columns=["id", "date", "exercise", "weight"])

# Save workout records to a JSON file
def save_workout_records(workout_records):
    with open(WORKOUT_RECORDS_FILE, "w") as f:
        json.dump(workout_records.to_dict(orient='records'), f)

# Initialize session state for user login status and credentials
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.current_user = None
    st.session_state.current_email = None
    st.session_state.workout_records = load_workout_records()  # Load the workout records from file

# Register a new user
def register_user(username, email, password):
    user_db = load_user_db()
    if username in user_db:
        return "Username already exists!"
    elif email in [user["email"] for user in user_db.values()]:
        return "Email is already registered!"
    else:
        user_db[username] = {"email": email, "password": password}
        save_user_db(user_db)
        return "User registered successfully!"

# Login a user (by username or email)
def login_user(identifier, password):
    user_db = load_user_db()
    # Check if identifier is username or email
    user_found = None
    for username, user_info in user_db.items():
        if username == identifier or user_info["email"] == identifier:
            user_found = (username, user_info)
            break

    if not user_found:
        return "Username or email not found!"
    elif user_found[1]["password"] != password:
        return "Incorrect password!"
    else:
        return user_found[0]  # Return the username on successful login

# Logout the current user
def logout_user():
    st.session_state.logged_in = False
    st.session_state.current_user = None
    st.session_state.current_email = None
    st.session_state.workout_records = load_workout_records()  # Reload the workout records

# Handle register/login
if not st.session_state.logged_in:
    st.title("Gym Progress Tracker - Register / Login")
    
    choice = st.selectbox("Choose an option", ["Login", "Register"])
    
    if choice == "Register":
        st.subheader("Create a new account")
        username = st.text_input("Username")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        
        if st.button("Register"):
            if username and email and password and confirm_password:
                if password != confirm_password:
                    st.error("Passwords do not match!")
                else:
                    result = register_user(username, email, password)
                    if "success" in result:
                        st.success(result)
                    else:
                        st.error(result)
            else:
                st.error("Please fill in all fields.")
    
    elif choice == "Login":
        st.subheader("Login")
        identifier = st.text_input("Username or Email")
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            if identifier and password:
                result = login_user(identifier, password)
                if "not found" in result or "Incorrect" in result:
                    st.error(result)
                else:
                    st.session_state.logged_in = True
                    st.session_state.current_user = result
                    st.session_state.current_email = load_user_db()[result]["email"]
                    st.success(f"Hello, {result}! You have successfully logged in.")
            else:
                st.error("Please fill in all fields.")

# If logged in, show a simple greeting page
if st.session_state.logged_in:
    st.title(f"Hello, {st.session_state.current_user}!")

    # Add workout record section
    st.header("Add Workout Record")
    exercises = [
        "Incline Smith Machine Bench Press", 
        "Machine Pec Fly",
        "Smith Machine Shoulder Press",
        "Machine Lat Row",
        "Machine Upper Back Row", 
        "Pulldown", 
        "Carter Extensions", 
        "Preacher Curls", 
        "Machine Lateral Raise", 
        "S/A Standing Rear Delt Fly", 
        "Squats", 
        "Lying Hamstring Curl", 
        "Standing Hamstring Curl", 
        "Abductors Machine", 
        "Leg Extensions", 
        "Calf Raises", 
        "Standing Traps Shrugs"
    ]
    selected_exercise = st.selectbox("Select Exercise", exercises)
    input_weight = st.number_input("Enter Weight", min_value=0.0, step=0.5)

    if st.button("Add Record"):
        if selected_exercise and input_weight > 0:
            new_id = len(st.session_state.workout_records) + 1
            new_record = {
                "id": new_id,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "exercise": selected_exercise,
                "weight": input_weight
            }
            new_record_df = pd.DataFrame([new_record])  # Convert to DataFrame
            st.session_state.workout_records = pd.concat([st.session_state.workout_records, new_record_df], ignore_index=True)
            save_workout_records(st.session_state.workout_records)  # Save updated records to file
            st.success(f"Record for {selected_exercise} with weight {input_weight} added.")
        else:
            st.error("Please enter a valid weight.")
    
    # Graph for workout progression
    st.header("Workout Progression Graph")
    graph_data = st.session_state.workout_records.groupby(["exercise", "date"])["weight"].max().reset_index()

    if not graph_data.empty:
        fig, ax = plt.subplots(figsize=(10, 6))

        for exercise in graph_data["exercise"].unique():
            exercise_data = graph_data[graph_data["exercise"] == exercise]
            ax.plot(exercise_data["date"], exercise_data["weight"], label=exercise)
        
        # Customize the graph's background and remove grid squares
        ax.set_facecolor('black')
        ax.grid(False)  # Remove the grid squares
        ax.set_xlabel("Date")
        ax.set_ylabel("Weight")
        ax.set_title("Workout Progression")
        ax.legend()

        # Rotate x-axis labels for better readability
        plt.xticks(rotation=45)
        st.pyplot(fig)
    else:
        st.write("No workout data available for plotting.")

    # View and Delete records section (only for the selected exercise)
    st.header("View and Delete Records")
    
    # Filter the records based on the selected exercise
    filtered_records = st.session_state.workout_records[st.session_state.workout_records["exercise"] == selected_exercise]
    
    if not filtered_records.empty:
        st.dataframe(filtered_records)
        
        # Select records to delete
        ids_to_delete = st.multiselect("Select record IDs to delete", options=filtered_records["id"].tolist())
        if st.button("Delete Selected Records"):
            if ids_to_delete:
                st.session_state.workout_records = st.session_state.workout_records[~st.session_state.workout_records["id"].isin(ids_to_delete)]
                save_workout_records(st.session_state.workout_records)  # Save updated records to file
                st.success("Selected records deleted.")
            else:
                st.error("No records selected to delete.")
    else:
        st.write(f"No records found for {selected_exercise}.")
    
    # Logout button
    if st.button("Logout"):
        logout_user()
        st.success("You have been logged out.")
