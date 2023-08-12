import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
from supabase import create_client, Client
import requests
from io import BytesIO
import matplotlib.pyplot as plt
from collections import defaultdict

st.set_page_config(page_title="Teacher", page_icon="👤")

# Initialize connection.
# Uses st.cache_resource to only run once.
@st.cache_resource
def init_connection():
    url = st.secrets["supabase_url"]
    key = st.secrets["supabase_key"]
    return create_client(url, key)

supabase = init_connection()

# --- USER AUTHENTICATION ---

with open('config.yaml', encoding='utf-8') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['preauthorized']
)

name, authentication_status, username = authenticator.login("Login", "main")

if "authentication_status" not in st.session_state:
    st.session_state["authentication_status"] = None  # or your default value

if st.session_state["authentication_status"]:
    authenticator.logout('Logout', 'sidebar', key='unique_key')
    if username == 'quangnguyen':
        name = st.session_state['name']
        username = st.session_state['username']

        st.write('## Student Homework Submissions 📋')
        st.write('\n\n\n\n')

        @st.cache_data(ttl=600)
        def run_query():
            return supabase.table("eh_speaking_hw").select("*").execute()

        rows = run_query()
        user_and_lesson_data = rows.data

        user_classes = list({data['user_class'] for data in user_and_lesson_data})
        selected_user_class = st.selectbox('Select a class', user_classes)

        if selected_user_class:
            names_for_class = list({data['name'] for data in user_and_lesson_data if data['user_class'] == selected_user_class})
            selected_name = st.selectbox('Select a student', names_for_class)

        if selected_user_class and selected_name:
            lessons_for_name = list({data['lesson_number'] for data in user_and_lesson_data if data['name'] == selected_name and data['user_class'] == selected_user_class})
            selected_lesson = st.selectbox('Select a lesson', lessons_for_name)

        st.write('\n\n\n\n')
        mispronunciations = []
        fluency_scores = []
        pron_scores = []
        for item in user_and_lesson_data:
            if item['name'] == selected_name and item['user_class'] == selected_user_class and item['lesson_number']==selected_lesson:
                st.write(f"**{item['question'].upper()}**")
                st.write(f"*{item['user_answer']}*")
                # Get a URL from your selected data
                user_audio_url = item['user_audio']

                # Get the file data from the URL
                response = requests.get(user_audio_url)

                # Wrap the BytesIO object with the audio file
                audio_bytes = BytesIO(response.content)

                st.audio(audio_bytes.read(), format="audio/wav")
                st.write(f":violet[**AI-enhanced**] ✨ {item['improved_answer']}")
                st.write(f"{item['idiomatic_exp']}")
                if item['mispronunciation']:
                    mispronunciations.extend(item['mispronunciation'].split(', '))
                fluency_scores.append(float(item['fluency_score']))
                pron_scores.append(float(item['pron_score']))

                st.divider()
        
        st.write('#### Average pronunciation scores')
        col1, col2 = st.columns([1, 1])

        average_fluency = sum(fluency_scores) / len(fluency_scores)
        col1.metric("Fluency", f"{average_fluency:.1f}")

        average_pronunciation = sum(pron_scores) / len(pron_scores)
        col2.metric("Pronunciation", f"{average_pronunciation:.1f}")

        # Gather scores in a dictionary, keyed by lesson number, and convert "Lesson #" to #
        scores_by_lesson = defaultdict(lambda: {'fluency': [], 'pron': []})
        for item in [d for d in user_and_lesson_data if d['name'] == selected_name and d['user_class'] == selected_user_class]:
            lesson_number = int(item['lesson_number'].split(" ")[1])  # "Lesson #" to #
            scores_by_lesson[lesson_number]['fluency'].append(float(item['fluency_score']))
            scores_by_lesson[lesson_number]['pron'].append(float(item['pron_score']))

        # Compute average scores for each lesson
        avg_fluency_by_lesson = [sum(val['fluency'])/len(val['fluency']) for key, val in sorted(scores_by_lesson.items())]
        avg_pron_by_lesson = [sum(val['pron'])/len(val['pron']) for key, val in sorted(scores_by_lesson.items())]

        fig, ax = plt.subplots()

        # Plot average fluency and pronunciation scores over lessons
        ax.plot(range(1, len(avg_fluency_by_lesson) + 1), avg_fluency_by_lesson, 'o-', label='Avg Fluency scores')
        ax.plot(range(1, len(avg_pron_by_lesson) + 1), avg_pron_by_lesson, 'o-', label='Avg Pron scores')

        ax.legend()
        ax.set_xlabel('Lesson')
        ax.set_ylabel('Average Score')
        ax.set_title(f'Average scores over lessons for {selected_name}')

        st.pyplot(fig)


        st.write('#### Potential mispronunciations')
        st.write(", ".join(mispronunciations))
    else:
        st.warning("You need to be a teacher to see this page.")

elif st.session_state["authentication_status"] is False:
    st.error('Username/password is incorrect')
elif st.session_state["authentication_status"] is None:
    st.warning('Please enter your username and password')
