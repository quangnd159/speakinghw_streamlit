import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
from st_supabase_connection import SupabaseConnection
import requests
from io import BytesIO

st.set_page_config(page_title="Teacher", page_icon="👩🏻‍🏫")

st_supabase_client = st.experimental_connection(
    name="supabase_connection",
    type=SupabaseConnection,
    ttl=None,
    url=st.secrets["supabase_url"],
    key=st.secrets["supabase_key"],
)

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
    st.session_state["authentication_status"] = None

if st.session_state["authentication_status"]:
    authenticator.logout('Logout', 'sidebar', key='unique_key')
    if username == 'quangnguyen' or username == 'msmai':
        name = st.session_state['name']
        username = st.session_state['username']

        st.write('## Student Homework Submissions 📋')
        st.write('\n\n\n\n')

        # Class selection
        user_classes = list({row['user_class'] for row in st_supabase_client.query("user_class", table="eh_speaking_hw", ttl=600).execute().data})
        selected_user_class = st.selectbox('Select a class', user_classes)

        if selected_user_class:
            # Lesson selection for a particular class
            lessons_for_class = list({row['lesson_number'] for row in st_supabase_client.query("lesson_number", table="eh_speaking_hw").eq("user_class", selected_user_class).execute().data})
            selected_lesson = st.selectbox('Select a lesson', lessons_for_class)
            
            if selected_lesson:
                # Name selection for a particular class and lesson
                names_for_class_and_lesson = list({row['name'] for row in st_supabase_client.query("name", table="eh_speaking_hw").eq("user_class", selected_user_class).eq("lesson_number", selected_lesson).execute().data})
                selected_name = st.selectbox('Select a student', names_for_class_and_lesson)

                if selected_name:
                    # Fetch data for selected name, class and lesson
                    user_and_lesson_data_filtered = st_supabase_client.query("*", table="eh_speaking_hw").eq("user_class", selected_user_class).eq("lesson_number", selected_lesson).eq("name", selected_name).execute().data
                    
                    mispronunciations = []
                    fluency_scores = []
                    pron_scores = []

                    for item in user_and_lesson_data_filtered:
                        st.write(f"**{item['question'].upper()}**")
                        st.write(f"*{item['user_answer']}*")
                        user_audio_url = item['user_audio']
                        response = requests.get(user_audio_url)
                        audio_bytes = BytesIO(response.content)
                        st.audio(audio_bytes.read(), format="audio/wav")
                        st.write(f":violet[**AI-enhanced**] ✨ {item['improved_answer']}")
                        st.write(f"{item['idiomatic_exp']}")
                        if item['mispronunciation']:
                            mispronunciations.extend(item['mispronunciation'].split(', '))
                        fluency_scores.append(float(item['fluency_score']))
                        pron_scores.append(float(item['pron_score']))
                        st.divider()                    

        st.write('\n\n\n\n')

        st.write('#### Pronunciation scores')
        col1, col2 = st.columns([1, 1])

        average_fluency = sum(fluency_scores) / len(fluency_scores) if fluency_scores else 0
        col1.metric("Fluency", f"{average_fluency:.1f}")

        average_pronunciation = sum(pron_scores) / len(pron_scores) if pron_scores else 0
        col2.metric("Pronunciation", f"{average_pronunciation:.1f}")

        st.write('#### Potential mispronunciations')
        st.write(", ".join(mispronunciations))
    else:
        st.warning("Only teachers can access this page.")

elif st.session_state["authentication_status"] is False:
    st.error('Username/password is incorrect')
elif st.session_state["authentication_status"] is None:
    st.warning('Please enter your username and password')
