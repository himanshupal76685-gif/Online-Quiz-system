import json
import os
import time
import streamlit as st

DB_FILE = "database.json"

# --- DATABASE FUNCTIONS ---
def load_data():
    default_data = {
        "users": {
            "admin": {"password": "adminpassword", "role": "admin"},
            "student1": {"password": "password123", "role": "student"}
        },
        "questions": [
            {
                "id": 1,
                "category": "Python",
                "question": "Which of the following is used to define a block of code in Python?",
                "options": ["Indentation", "Key", "Brackets", "Parentheses"],
                "answer": "Indentation"
            },
            {
                "id": 2,
                "category": "Python",
                "question": "What is the output of type(10) in Python?",
                "options": ["float", "int", "number", "double"],
                "answer": "int"
            },
            {
                "id": 3,
                "category": "General Knowledge",
                "question": "What is the capital of France?",
                "options": ["London", "Berlin", "Paris", "Madrid"],
                "answer": "Paris"
            }
        ]
    }
    
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w") as f:
            json.dump(default_data, f, indent=4)
        return default_data
    
    try:
        with open(DB_FILE, "r") as f:
            data = json.load(f)
            if "users" not in data:
                data["users"] = default_data["users"]
            if "questions" not in data:
                data["questions"] = default_data["questions"]
            return data
    except Exception:
        return default_data

def save_data(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

# --- APP CONFIGURATION & STYLING ---
st.set_page_config(page_title="Pro Quiz Application", page_icon="🎯", layout="centered")

# Custom CSS for Modern UI
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: bold;
        border: none;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #5a6fd6 0%, #684190 100%);
        color: #fff;
    }
    div.stMetric {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

# Initialize Session State
if "user" not in st.session_state:
    st.session_state.user = None
if "role" not in st.session_state:
    st.session_state.role = None

# --- AUTHENTICATION & REGISTRATION ---
def auth_page():
    st.title("🎯 Pro Quiz Platform")
    st.info("💡 **Demo Accounts:** Admin -> `admin` / `adminpassword` | Student -> `student1` / `password123`")
    
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])
    
    with tab1:
        st.subheader("Login to your account")
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login Now"):
            data = load_data()
            if username in data["users"] and data["users"][username]["password"] == password:
                st.session_state.user = username
                st.session_state.role = data["users"][username]["role"]
                st.success(f"Welcome back, {username}!")
                st.rerun()
            else:
                st.error("Invalid username or password")

    with tab2:
        st.subheader("Create a new Student account")
        new_user = st.text_input("Choose Username", key="reg_user")
        new_pass = st.text_input("Choose Password", type="password", key="reg_pass")
        if st.button("Register Account"):
            data = load_data()
            if not new_user or not new_pass:
                st.warning("Please fill in all fields.")
            elif new_user in data["users"]:
                st.error("Username already exists!")
            else:
                data["users"][new_user] = {"password": new_pass, "role": "student"}
                save_data(data)
                st.success("Registration successful! Please switch to the Login tab.")

# --- ADMIN PANEL ---
def admin_panel():
    st.title("👨‍💼 Admin Dashboard")
    st.write(f"Logged in as: **{st.session_state.user}**")
    
    data = load_data()
    menu = st.sidebar.selectbox("Admin Menu", ["Manage Questions", "Add Question"])

    if menu == "Manage Questions":
        st.subheader("Existing Questions")
        if not data["questions"]:
            st.info("No questions available.")
        for idx, q in enumerate(data["questions"]):
            with st.expander(f"Q{idx+1}: {q['question']} (Cat: {q['category']})"):
                st.write(f"**Options:** {', '.join(q['options'])}")
                st.write(f"**Answer:** {q['answer']}")
                if st.button(f"Delete Question {q['id']}", key=f"del_{q['id']}"):
                    data["questions"] = [item for item in data["questions"] if item["id"] != q["id"]]
                    save_data(data)
                    st.success("Question deleted successfully!")
                    st.rerun()

    elif menu == "Add Question":
        st.subheader("Add a New Question")
        cat = st.text_input("Category (e.g., Python, GK)")
        q_text = st.text_area("Question Text")
        opt1 = st.text_input("Option 1")
        opt2 = st.text_input("Option 2")
        opt3 = st.text_input("Option 3")
        opt4 = st.text_input("Option 4")
        ans = st.selectbox("Correct Answer", [opt1, opt2, opt3, opt4] if opt1 and opt2 else [])

        if st.button("Save Question"):
            if not cat or not q_text or not opt1 or not opt2:
                st.warning("Please fill out all mandatory fields.")
            else:
                current_data = load_data()
                new_id = max([q["id"] for q in current_data["questions"]], default=0) + 1
                new_q = {
                    "id": new_id,
                    "category": cat,
                    "question": q_text,
                    "options": [opt1, opt2, opt3, opt4],
                    "answer": ans
                }
                current_data["questions"].append(new_q)
                save_data(current_data)
                st.success("Question added successfully!")

    if st.button("Logout"):
        st.session_state.user = None
        st.session_state.role = None
        st.rerun()

# --- STUDENT QUIZ PLATFORM WITH TIMER & SHUFFLE ---
def student_panel():
    st.title("📚 Student Quiz Portal")
    st.write(f"Welcome, **{st.session_state.user}**!")
    
    data = load_data()
    questions = data["questions"]

    if not questions:
        st.warning("No quizzes available right now. Check back later!")
        if st.button("Logout"):
            st.session_state.user = None
            st.session_state.role = None
            st.rerun()
        return

    categories = list(set([q["category"] for q in questions]))
    selected_cat = st.selectbox("Select Quiz Category", categories)

    filtered_questions = [q for q in questions if q["category"] == selected_cat]

    if st.button("🚀 Start Quiz (with Timer)"):
        st.session_state.active_quiz = filtered_questions
        st.session_state.current_q_index = 0
        st.session_state.user_answers = {}
        st.session_state.quiz_submitted = False
        # Set a 60 seconds timer for the quiz block
        st.session_state.quiz_start_time = time.time()
        st.session_state.time_limit = 60 
        st.rerun()

    if "active_quiz" in st.session_state and st.session_state.active_quiz:
        q_list = st.session_state.active_quiz
        idx = st.session_state.current_q_index

        # Timer calculation
        elapsed_time = int(time.time() - st.session_state.quiz_start_time)
        time_left = st.session_state.time_limit - elapsed_time

        if time_left <= 0 and not st.session_state.quiz_submitted:
            st.warning("⏰ Time's up! Your quiz has been auto-submitted.")
            st.session_state.quiz_submitted = True
            st.rerun()

        if not st.session_state.quiz_submitted:
            # Display Timer in sidebar or top bar
            st.sidebar.markdown("### ⏱️ Time Remaining")
            st.sidebar.metric(label="Seconds Left", value=max(0, time_left))

            st.markdown(f"### Question {idx + 1} of {len(q_list)}")
            current_q = q_list[idx]
            st.write(f"**{current_q['question']}**")

            default_ans = st.session_state.user_answers.get(current_q["id"], None)
            try:
                default_idx = current_q["options"].index(default_ans) if default_ans in current_q["options"] else 0
            except ValueError:
                default_idx = 0

            selected_opt = st.radio("Choose an option:", current_q["options"], index=default_idx, key=f"q_{current_q['id']}")

            st.session_state.user_answers[current_q["id"]] = selected_opt

            col1, col2 = st.columns(2)
            with col1:
                if idx > 0 and st.button("⬅️ Previous"):
                    st.session_state.current_q_index -= 1
                    st.rerun()
            with col2:
                if idx < len(q_list) - 1:
                    if st.button("Next ➡️"):
                        st.session_state.current_q_index += 1
                        st.rerun()
                else:
                    if st.button("✅ Submit Quiz"):
                        st.session_state.quiz_submitted = True
                        st.rerun()
        else:
            # --- RESULT PAGE ---
            st.subheader("📊 Quiz Performance & Results")
            score = 0
            total = len(q_list)

            for q in q_list:
                user_ans = st.session_state.user_answers.get(q["id"])
                if user_ans == q["answer"]:
                    score += 1

            percentage = (score / total) * 100

            col_a, col_b = st.columns(2)
            with col_a:
                st.metric(label="Final Score", value=f"{score} / {total}")
            with col_b:
                st.metric(label="Percentage", value=f"{percentage:.2f}%")

            if percentage >= 50:
                st.success("🎉 Outstanding! You passed the quiz successfully.")
            else:
                st.error("❌ Don't worry! Review the material and try again.")

            if st.button("🔄 Restart / Attempt Another Quiz"):
                del st.session_state.active_quiz
                del st.session_state.current_q_index
                del st.session_state.user_answers
                del st.session_state.quiz_submitted
                st.rerun()

    if st.button("Logout"):
        st.session_state.clear()
        st.rerun()

# --- MAIN ROUTER ---
if st.session_state.user is None:
    auth_page()
elif st.session_state.role == "admin":
    admin_panel()
else:
    student_panel()
