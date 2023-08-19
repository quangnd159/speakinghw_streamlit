import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
# from supabase import create_client, Client

from st_supabase_connection import SupabaseConnection

st.set_page_config(page_title="Collocations", page_icon="🌱")

# @st.cache_resource
# def init_connection():
#     url = st.secrets["supabase_url"]
#     key = st.secrets["supabase_key"]
#     return create_client(url, key)

# supabase = init_connection()

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

    name = st.session_state['name']
    username = st.session_state['username']

    st.write('## Collocations')
    st.write(':green[Collections are natural combinations of words. They are are essential for speaking and writing in a natural way.]')

    # @st.cache_data(ttl=600)
    # def run_query():
    #     return st_supabase_client.table("eh_speaking_hw").select("idiomatic_exp").execute()

    # rows = run_query()
    # collocation_data = rows.data

    collocations = st_supabase_client.query("idiomatic_exp", table="eh_speaking_hw", ttl=600).execute()

    for item in collocations.data:
        st.write(f"{item['idiomatic_exp']}")

elif st.session_state["authentication_status"] is False:
    st.error('Username/password is incorrect')
elif st.session_state["authentication_status"] is None:
    st.warning('Please enter your username and password')
