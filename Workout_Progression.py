import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os
import matplotlib.pyplot as plt

# Paths to store the user credentials and workout records files
USER_DB_FILE = "user_db.json"
WORKOUT_RECORDS_FILE = "workout_records.json"

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
        with st.form(key="register_form"):
            username = st.text_input("Username")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            submit_button = st.form_submit_button("Register")
        
            if submit_button:
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
        with st.form(key="login_form"):
            identifier = st.text_input("Username or Email")
            password = st.text_input("Password", type="password")
            submit_button = st.form_submit_button("Login")
        
            if submit_button:
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
    with st.form(key="add_workout_form"):
        selected_exercise = st.selectbox("Select Exercise", exercises)
        input_weight = st.number_input("Enter Weight", min_value=0.0, step=0.5)
        submit_button = st.form_submit_button("Add Record")

        if submit_button:
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
    
    # View and Delete records section (only for the selected exercise)
    st.header("View and Delete Records")
    
    # Filter the records based on the selected exercise
    filtered_records = st.session_state.workout_records[st.session_state.workout_records["exercise"] == selected_exercise]
    
    if not filtered_records.empty:
        st.dataframe(filtered_records)
        
        # Select records to delete
        with st.form(key="delete_records_form"):
            ids_to_delete = st.multiselect("Select record IDs to delete", options=filtered_records["id"].tolist())
            submit_button = st.form_submit_button("Delete Selected Records")

            if submit_button:
                if ids_to_delete:
                    st.session_state.workout_records = st.session_state.workout_records[~st.session_state.workout_records["id"].isin(ids_to_delete)]
                    save_workout_records(st.session_state.workout_records)  # Save updated records to file
                    st.success("Selected records deleted.")
                else:
                    st.error("No records selected to delete.")
    else:
        st.write(f"No records found for {selected_exercise}.")
    
    # Graph Progression Section
    st.header("View Weight Progression")
    
    if not filtered_records.empty:
        # Sort by date
        filtered_records["date"] = pd.to_datetime(filtered_records["date"])
        filtered_records = filtered_records.sort_values("date")

        # Plotting the graph of weight progression over time
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(filtered_records["date"], filtered_records["weight"], marker='o', linestyle='-', color='b')

        ax.set_title(f"Weight Progression for {selected_exercise}")
        ax.set_xlabel("Date")
        ax.set_ylabel("Weight (kg)")
        ax.grid(True)

        st.pyplot(fig)
    else:
        st.write("No records available to plot progression.")
    
    # Logout button
    with st.form(key="logout_form"):
        submit_button = st.form_submit_button("Logout")

        if submit_button:
            logout_user()
            st.success("You have been logged out.")
