import json
import os
import streamlit as st

DB_FILE = "database.json"

# --- DATABASE FUNCTIONS ---
def load_data():
    if not os.path.exists(DB_FILE):
        default_data = {
            "users": {"admin": {"password": "adminpassword", "role": "admin"}},
            "questions": []
        }
        with open(DB_FILE, "w") as f:
            json.dump(default_data, f, indent=4)
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

# --- APP CONFIGURATION ---
st.set_page_title_id = "Quiz Application"
st.set_page_config(page_title="Interactive Quiz App", page_icon="🧠", layout="centered")

# Initialize Session State
if "user" not in st.session_state:
    st.session_state.user = None
if "role" not in st.session_state:
    st.session_state.role = None
if "page" not in st.session_state:
    st.session_state.page = "Login"

# --- AUTHENTICATION & REGISTRATION ---
def auth_page():
    st.title("🧠 Welcome to Quiz Platform")
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    data = load_data()

    with tab1:
        st.subheader("Login to your account")
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login"):
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
        if st.button("Register"):
            if not new_user or not new_pass:
                st.warning("Please fill in all fields.")
            elif new_user in data["users"]:
                st.error("Username already exists!")
            else:
                data["users"][new_user] = {"password": new_pass, "role": "student"}
                save_data(data)
                st.success("Registration successful! Please login.")

# --- ADMIN PANEL ---
def admin_panel():
    st.title("👨‍💼 Admin Dashboard")
    st.write(f"Logged in as: **{st.session_state.user}**")
    
    data = load_data()
    
    menu = st.sidebar.selectbox("Admin Menu", ["View/Delete Questions", "Add Question"])

    if menu == "View/Delete Questions":
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
        ans = st.selectbox("Correct Answer", [opt1, opt2, opt3, opt4])

        if st.button("Save Question"):
            if not cat or not q_text or not opt1 or not opt2:
                st.warning("Please fill out all fields.")
            else:
                new_id = max([q["id"] for q in data["questions"]], default=0) + 1
                new_q = {
                    "id": new_id,
                    "category": cat,
                    "question": q_text,
                    "options": [opt1, opt2, opt3, opt4],
                    "answer": ans
                }
                data["questions"].append(new_q)
                save_data(data)
                st.success("Question added successfully!")

    if st.button("Logout"):
        st.session_state.user = None
        st.session_state.role = None
        st.rerun()

# --- STUDENT QUIZ PLATFORM ---
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

    # Select Category
    categories = list(set([q["category"] for q in questions]))
    selected_cat = st.selectbox("Select Quiz Category", categories)

    filtered_questions = [q for q in questions if q["category"] == selected_cat]

    if st.button("Start Quiz"):
        st.session_state.active_quiz = filtered_questions
        st.session_state.current_q_index = 0
        st.session_state.user_answers = {}
        st.session_state.quiz_submitted = False
        st.rerun()

    if "active_quiz" in st.session_state and st.session_state.active_quiz:
        q_list = st.session_state.active_quiz
        idx = st.session_state.current_q_index

        if not st.session_state.quiz_submitted:
            st.markdown(f"### Question {idx + 1} of {len(q_list)}")
            current_q = q_list[idx]
            st.write(f"**{current_q['question']}**")

            # Maintain previous selection if available
            default_ans = st.session_state.user_answers.get(current_q["id"], None)
            selected_opt = st.radio("Choose an option:", current_q["options"], index=current_q["options"].index(default_ans) if default_ans in current_q["options"] else 0, key=f"q_{current_q['id']}")

            st.session_state.user_answers[current_q["id"]] = selected_opt

            col1, col2 = st.columns(2)
            with col1:
                if idx > 0 and st.button("Previous"):
                    st.session_state.current_q_index -= 1
                    st.rerun()
            with col2:
                if idx < len(q_list) - 1:
                    if st.button("Next"):
                        st.session_state.current_q_index += 1
                        st.rerun()
                else:
                    if st.button("Submit Quiz"):
                        st.session_state.quiz_submitted = True
                        st.rerun()
        else:
            # --- RESULT PAGE ---
            st.subheader("📊 Quiz Results")
            score = 0
            total = len(q_list)

            for q in q_list:
                user_ans = st.session_state.user_answers.get(q["id"])
                if user_ans == q["answer"]:
                    score += 1

            percentage = (score / total) * 100

            st.metric(label="Your Score", value=f"{score} / {total}")
            st.metric(label="Percentage", value=f"{percentage:.2f}%")

            if percentage >= 50:
                st.success("🎉 Congratulations! You passed the quiz.")
            else:
                st.error("❌ Keep practicing! You can do better.")

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