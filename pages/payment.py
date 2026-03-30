import streamlit as st

st.set_page_config(
    page_title="Class Payment Form",
    page_icon="💳",
    layout="wide"
)

def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    f.close()

local_css("assets/style.css")

st.title("Class Booking")
st.subheader("Your selected course:")

if "selected_course" in st.session_state:
    course = st.session_state["selected_course"]
    st.write(f"Title: {course["title"]}")
    st.write(f"Price: {course["cost"]}")
else:
    st.write("No course selected. Please return to the main page and click the 'Book this class' button to book a course!")
    st.stop()

st.divider()

st.subheader("Your details:")

with st.form("booking_form"):
    name = st.text_input("Full Name:")
    email = st.text_input("Email Address:")
    requirements = st.text_area("Additional Requirements",placeholder="Let us know about any accessibility requirements or additional needs (optional)")

    submitted = st.form_submit_button("Confirm booking")

    if submitted:
        if not name or not email:
            st.error("Please fill in all required fields")
        elif "@" not in email or "." not in email:
            st.error("Please enter a valid email address.")
        else:
            st.success(f"Booking confirmed! A confirmation email has been sent to {email}")
    
blank_col, cancel_col = st.columns([3,2])
with cancel_col:
    cancelled = st.button("Cancel booking",type="primary",width="stretch")
    if cancelled:
            del st.session_state["selected_course"]
            st.switch_page("./app.py")