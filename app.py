import os
from dotenv import load_dotenv
import streamlit as st
from pathlib import Path
from typing import Optional
from langchain.agents import create_sql_agent
from langchain.sql_database import SQLDatabase
from langchain.agents.agent_types import AgentType
from langchain.callbacks import StreamlitCallbackHandler
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from sqlalchemy import create_engine
import sqlite3
from langchain_groq import ChatGroq

# Load environment variables
load_dotenv()

# Constants
DEFAULT_MODEL = "Llama3-8b-8192"
DB_OPTIONS = {
    "sqlite": "Use SQLite 3 Database - Student.db",
    "mysql": "Connect to your MySQL Database"
}

# Configuration
st.set_page_config(page_title="ChatSQL: Chat with SQL DB", page_icon="🦜")
st.title("🦜 ChatSQL: Chat with SQL DB")

LOCALDB="USE_LOCALDB"
MYSQL="USE_MYSQL"

def init_session_state():
    """Initialize session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "How can I help you?"}]

def get_db_credentials() -> dict:
    """Get database credentials from environment variables or sidebar."""
    credentials = {
        "api_key": st.sidebar.text_input(
            "Groq API Key",
            value=os.getenv("GROQ_API_KEY", "GROQ_API_KEY"),
            type="password"
        )
    }
    
    selected_opt = st.sidebar.radio(
        "Choose the DB which you want to chat",
        options=list(DB_OPTIONS.values())
    )
    
    if DB_OPTIONS["mysql"] == selected_opt:
        credentials.update({
            "db_uri": MYSQL,
            "mysql_host": st.sidebar.text_input("MySQL Host", value=os.getenv("MYSQL_HOST", "")),
            "mysql_user": st.sidebar.text_input("MySQL User", value=os.getenv("MYSQL_USER", "")),
            "mysql_password": st.sidebar.text_input("MySQL password", type="password", value=os.getenv("MYSQL_PASSWORD", "")),
            "mysql_db": st.sidebar.text_input("MySQL database", value=os.getenv("MYSQL_DB", ""))
        })
    else:
        credentials.update({"db_uri": LOCALDB})
    
    return credentials

@st.cache_resource(ttl="2h")
def configure_db(db_uri,mysql_host=None,mysql_user=None,mysql_password=None,mysql_db=None):
    if db_uri==LOCALDB:
        dbfilepath=(Path(__file__).parent/"student.db").absolute()
        print(dbfilepath)
        creator = lambda: sqlite3.connect(f"file:{dbfilepath}?mode=ro", uri=True)
        return SQLDatabase(create_engine("sqlite:///", creator=creator))
    elif db_uri==MYSQL:
        if not (mysql_host and mysql_user and mysql_password and mysql_db):
            st.error("Please provide all MySQL connection details.")
            st.stop()
        return SQLDatabase(create_engine(f"mysql+mysqlconnector://{mysql_user}:{mysql_password}@{mysql_host}/{mysql_db}"))   
    
def create_chat_agent(db: SQLDatabase, api_key: str):
    """Create and configure the SQL chat agent."""
    if not api_key:
        st.error("Please provide a Groq API key.")
        st.stop()
        
    llm = ChatGroq(
        groq_api_key=api_key,
        model_name=DEFAULT_MODEL,
        streaming=True
    )
    
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)
    
    return create_sql_agent(
        llm=llm,
        toolkit=toolkit,
        verbose=True,
        handle_parsing_errors=True,
        agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION
    )

def main():
    init_session_state()
    credentials = get_db_credentials()
    
    if not credentials["api_key"]:
        st.info("Please add the Groq API key")
        return
        
    try:
        if credentials["db_uri"] == MYSQL:
            db = configure_db(
                credentials["db_uri"],
                credentials["mysql_host"],
                credentials["mysql_user"],
                credentials["mysql_password"],
                credentials["mysql_db"]
            )
        else:
            db = configure_db(credentials["db_uri"])
            
        agent = create_chat_agent(db, credentials["api_key"])
        
        # Display chat interface
        for msg in st.session_state.messages:
            st.chat_message(msg["role"]).write(msg["content"])

        user_query = st.chat_input(placeholder="Ask anything from the database")

        if user_query:
            st.session_state.messages.append({"role": "user", "content": user_query})
            st.chat_message("user").write(user_query)

            with st.chat_message("assistant"):
                streamlit_callback = StreamlitCallbackHandler(st.container())
                response = agent.run(user_query, callbacks=[streamlit_callback])
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.write(response)
                
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()

        


