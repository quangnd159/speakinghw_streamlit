import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
from supabase import create_client, Client
import requests
from io import BytesIO
import matplotlib.pyplot as plt
from collections import defaultdict

st.set_page_config(page_title="Profile", page_icon="👤")

@st.cache_resource
def init_connection():
    url = st.secrets["supabase_url"]
    key = st.secrets["supabase_key"]
    return create_client(url, key)

supabase = init_connection()

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

    name = st.session_state['name']
    username = st.session_state['username']

    st.write(f'## {name}\'s Profile')
    st.write('### Your work')

    @st.cache_data(ttl=600)
    def run_query():
        return supabase.table("eh_speaking_hw").select("*").execute()

    rows = run_query()
    user_and_lesson_data = [data for data in rows.data if data['username'] == username]

    lessons_for_name = list({data['lesson_number'] for data in user_and_lesson_data})
    selected_lesson = st.selectbox('Select a lesson', lessons_for_name)

    mispronunciations = []
    fluency_scores = []
    pron_scores = []
    for item in user_and_lesson_data:
        if item['lesson_number']==selected_lesson:
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
    
    st.write('### Average pronunciation scores')
    col1, col2 = st.columns([1, 1])
    average_fluency = sum(fluency_scores) / (len(fluency_scores) if len(fluency_scores) > 0 else 1)
    col1.metric("Fluency", f"{average_fluency:.1f}")
    average_pronunciation = sum(pron_scores) / (len(pron_scores) if len(pron_scores) > 0 else 1)
    col2.metric("Pronunciation", f"{average_pronunciation:.1f}")

    scores_by_lesson = defaultdict(lambda: {'fluency': [], 'pron': []})
    for item in user_and_lesson_data:
        lesson_number = int(item['lesson_number'].split(" ")[1])
        scores_by_lesson[lesson_number]['fluency'].append(float(item['fluency_score']))
        scores_by_lesson[lesson_number]['pron'].append(float(item['pron_score']))

    avg_fluency_by_lesson = [sum(val['fluency'])/len(val['fluency']) for key, val in sorted(scores_by_lesson.items())]
    avg_pron_by_lesson = [sum(val['pron'])/len(val['pron']) for key, val in sorted(scores_by_lesson.items())]

    fig, ax = plt.subplots()
    ax.plot(range(1, len(avg_fluency_by_lesson) + 1), avg_fluency_by_lesson, 'o-', label='Avg Fluency scores')
    ax.plot(range(1, len(avg_pron_by_lesson) + 1), avg_pron_by_lesson, 'o-', label='Avg Pron scores')

    ax.legend()
    ax.set_xlabel('Lesson')
    ax.set_ylabel('Average Score')
    ax.set_title(f'Average scores over lessons for {name}')

    st.pyplot(fig)

    st.write('#### Potential mispronunciations')
    st.write(", ".join(mispronunciations))

elif st.session_state["authentication_status"] is False:
    st.error('Username/password is incorrect')
elif st.session_state["authentication_status"] is None:
    st.warning('Please enter your username and password')
