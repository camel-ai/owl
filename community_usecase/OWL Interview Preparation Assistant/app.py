#app.py
import os
import streamlit as st
import logging
import queue
import time
import sys

# Add parent directory to path for OWL imports
sys.path.append('../')

try:
    from main import research_company, generate_interview_questions, create_interview_prep_plan
except ImportError as e:
    st.error(f"Error importing functions: {e}")
    st.stop()

# Setup logging with queue to capture logs for display
log_queue = queue.Queue()

class StreamlitLogHandler(logging.Handler):
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue
        self.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    def emit(self, record):
        log_entry = self.format(record)
        self.log_queue.put(log_entry)

# Configure root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)
root_logger.addHandler(StreamlitLogHandler(log_queue))
root_logger.addHandler(logging.StreamHandler())  # Also log to console

# Configure Streamlit page
st.set_page_config(
    page_title="Interview Prep Assistant(With OWL 🦉)", 
    page_icon="🦉",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-title {
        font-size: 2.5rem;
        color: #4a89dc;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-title {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .conversation-container {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        margin: 10px 0;
        padding: 10px;
        max-height: 500px;
        overflow-y: auto;
    }
    .user-message {
        background-color: #f0f7ff;
        border-left: 4px solid #4a89dc;
        padding: 10px;
        margin: 8px 0;
        border-radius: 4px;
    }
    .assistant-message {
        background-color: #f1f8e9;
        border-left: 4px solid #7cb342;
        padding: 10px;
        margin: 8px 0;
        border-radius: 4px;
    }
    .tool-call {
        background-color: #fff8e1;
        border: 1px solid #ffe0b2;
        padding: 8px;
        margin: 5px 0;
        border-radius: 4px;
        font-family: monospace;
        font-size: 0.9em;
    }
    .round-header {
        background-color: #e8eaf6;
        padding: 5px 10px;
        font-weight: bold;
        border-radius: 4px;
        margin: 15px 0 5px 0;
    }
    .final-answer {
        background-color: #e8f5e9;
        border-left: 5px solid #43a047;
        padding: 15px;
        margin: 15px 0;
        border-radius: 4px;
    }
    .metrics-container {
        display: flex;
        justify-content: space-around;
        margin: 15px 0;
        padding: 10px;
        background-color: #f5f5f5;
        border-radius: 4px;
    }
    .metric-box {
        text-align: center;
        padding: 8px 15px;
        background-color: white;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12);
    }
    .metric-value {
        font-size: 1.4rem;
        font-weight: bold;
        color: #4a89dc;
    }
    .metric-label {
        font-size: 0.8rem;
        color: #666;
    }
    .running-indicator {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 10px;
        margin: 15px 0;
        padding: 10px;
        background-color: #e3f2fd;
        border-radius: 4px;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.7; }
        100% { opacity: 1; }
    }
</style>
""", unsafe_allow_html=True)

def display_conversation(chat_history):
    """Display the conversation history in a structured format"""
    if not chat_history:
        st.info("No conversation available")
        return
    
    st.markdown("<div class='conversation-container'>", unsafe_allow_html=True)
    
    for idx, message in enumerate(chat_history):
        round_num = idx + 1
        st.markdown(f"<div class='round-header'>Round {round_num}</div>", unsafe_allow_html=True)
        
        # Display user message
        if "user" in message and message["user"]:
            st.markdown(f"<div class='user-message'><b>🧑‍💼 Job Seeker:</b><br>{message['user']}</div>", unsafe_allow_html=True)
        
        # Display assistant message
        if "assistant" in message and message["assistant"]:
            assistant_content = message["assistant"]
            # Remove any note about truncation for cleaner display
            if "[Note: This conversation was limited" in assistant_content:
                assistant_content = assistant_content.replace("[Note: This conversation was limited to maintain response quality. The complete thought process is available in the logs.]", "")
            
            st.markdown(f"<div class='assistant-message'><b>🦉 Interview Coach:</b><br>{assistant_content}</div>", unsafe_allow_html=True)
        
        # Display tool calls if any
        if "tool_calls" in message and message["tool_calls"]:
            for tool in message["tool_calls"]:
                tool_name = tool.get('name', 'Unknown Tool')
                st.markdown(f"<div class='tool-call'><b>🔧 Tool Used: {tool_name}</b></div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

def display_metrics(duration, token_count, num_rounds):
    """Display metrics in a visually appealing format"""
    st.markdown("<div class='metrics-container'>", unsafe_allow_html=True)
    
    # Time taken
    st.markdown(f"""
    <div class='metric-box'>
        <div class='metric-value'>{duration:.1f}s</div>
        <div class='metric-label'>Execution Time</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Token usage
    completion_tokens = token_count.get('completion_token_count', 0)
    prompt_tokens = token_count.get('prompt_token_count', 0)
    total_tokens = completion_tokens + prompt_tokens
    
    st.markdown(f"""
    <div class='metric-box'>
        <div class='metric-value'>{total_tokens:,}</div>
        <div class='metric-label'>Total Tokens</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Conversation rounds
    st.markdown(f"""
    <div class='metric-box'>
        <div class='metric-value'>{num_rounds}</div>
        <div class='metric-label'>Conversation Rounds</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

def get_logs():
    """Retrieve logs from the queue"""
    logs = []
    while not log_queue.empty():
        try:
            logs.append(log_queue.get_nowait())
        except queue.Empty:
            break
    return logs

def main():
    # Header
    st.markdown("<h1 class='main-title'>🦉 Interview Preparation Assistant</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-title'>Powered by multi-agent AI collaboration</p>", unsafe_allow_html=True)
    
    # Input section
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            job_role = st.text_input("Job Role", "Machine Learning Engineer")
        with col2:
            company_name = st.text_input("Company Name", "Google")
    
    # Main functionality tabs
    tab1, tab2, tab3, tab4 = st.tabs(["Company Research", "Interview Questions", "Preparation Plan", "System Logs"])
    
    # Tab 1: Company Research
    with tab1:
        st.header("🔍 Company Research")
        st.write("Get detailed insights about the company to help with your interview preparation.")
        
        if st.button("Research Company", use_container_width=True):
            with st.spinner():
                # Display running indicator
                status = st.empty()
                status.markdown("<div class='running-indicator'>🔄 Researching company information...</div>", unsafe_allow_html=True)
                
                # Progress bar
                progress = st.progress(0)
                
                # Progress callback
                def update_progress(current_round, max_rounds):
                    progress_value = min(current_round / max_rounds, 0.95)
                    progress.progress(progress_value)
                    status.markdown(f"<div class='running-indicator'>🔄 Processing conversation round {current_round}/{max_rounds}...</div>", unsafe_allow_html=True)
                
                # Execute research
                try:
                    start_time = time.time()
                    result = research_company(
                        company_name=company_name,
                        detailed=True,  # Always use detailed mode
                        limited_searches=False,  # Don't limit searches
                        progress_callback=update_progress
                    )
                    duration = time.time() - start_time
                    
                    # Update progress to complete
                    progress.progress(1.0)
                    status.markdown("<div class='running-indicator' style='background-color: #e8f5e9;'>✅ Research completed!</div>", unsafe_allow_html=True)
                    
                    # Display metrics
                    display_metrics(
                        duration=duration,
                        token_count=result["token_count"],
                        num_rounds=len(result["chat_history"])
                    )
                    
                    # Display final answer
                    st.subheader("📝 Research Results")
                    st.markdown(f"<div class='final-answer'>{result['answer']}</div>", unsafe_allow_html=True)
                    
                    # Display conversation
                    st.subheader("💬 Conversation Process")
                    display_conversation(result["chat_history"])
                    
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                    logging.exception("Error in company research")
    
    # Tab 2: Interview Questions
    with tab2:
        st.header("❓ Interview Questions")
        st.write("Generate tailored interview questions for your target role and company.")
        
        # Question type selector (adds interactivity but doesn't change behavior for now)
        question_type = st.radio(
            "Question Type",
            ["Technical", "Behavioral", "Company-Specific", "All"],
            horizontal=True
        )
        
        if st.button("Generate Questions", use_container_width=True):
            with st.spinner():
                # Display running indicator
                status = st.empty()
                status.markdown("<div class='running-indicator'>🔄 Creating interview questions...</div>", unsafe_allow_html=True)
                
                # Progress bar
                progress = st.progress(0)
                
                # Progress callback
                def update_progress(current_round, max_rounds):
                    progress_value = min(current_round / max_rounds, 0.95)
                    progress.progress(progress_value)
                    status.markdown(f"<div class='running-indicator'>🔄 Processing conversation round {current_round}/{max_rounds}...</div>", unsafe_allow_html=True)
                
                # Execute question generation
                try:
                    start_time = time.time()
                    result = generate_interview_questions(
                        job_role=job_role,
                        company_name=company_name,
                        detailed=True,  # Always use detailed mode
                        limited_searches=False,  # Don't limit searches
                        progress_callback=update_progress
                    )
                    duration = time.time() - start_time
                    
                    # Update progress to complete
                    progress.progress(1.0)
                    status.markdown("<div class='running-indicator' style='background-color: #e8f5e9;'>✅ Questions generated!</div>", unsafe_allow_html=True)
                    
                    # Display metrics
                    display_metrics(
                        duration=duration,
                        token_count=result["token_count"],
                        num_rounds=len(result["chat_history"])
                    )
                    
                    # Display final answer
                    st.subheader("📝 Generated Questions")
                    st.markdown(f"<div class='final-answer'>{result['answer']}</div>", unsafe_allow_html=True)
                    
                    # Display conversation
                    st.subheader("💬 Conversation Process")
                    display_conversation(result["chat_history"])
                    
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                    logging.exception("Error in question generation")
    
    # Tab 3: Preparation Plan
    with tab3:
        st.header("📋 Interview Preparation Plan")
        st.write("Create a comprehensive step-by-step plan to prepare for your interview.")
        
        if st.button("Create Preparation Plan", use_container_width=True):
            with st.spinner():
                # Display running indicator
                status = st.empty()
                status.markdown("<div class='running-indicator'>🔄 Creating preparation plan...</div>", unsafe_allow_html=True)
                
                # Progress bar
                progress = st.progress(0)
                
                # Progress callback
                def update_progress(current_round, max_rounds):
                    progress_value = min(current_round / max_rounds, 0.95)
                    progress.progress(progress_value)
                    status.markdown(f"<div class='running-indicator'>🔄 Processing conversation round {current_round}/{max_rounds}...</div>", unsafe_allow_html=True)
                
                # Execute plan creation
                try:
                    start_time = time.time()
                    result = create_interview_prep_plan(
                        job_role=job_role,
                        company_name=company_name,
                        detailed=True,  # Always use detailed mode
                        limited_searches=False,  # Don't limit searches
                        progress_callback=update_progress
                    )
                    duration = time.time() - start_time
                    
                    # Update progress to complete
                    progress.progress(1.0)
                    status.markdown("<div class='running-indicator' style='background-color: #e8f5e9;'>✅ Plan created!</div>", unsafe_allow_html=True)
                    
                    # Display metrics
                    display_metrics(
                        duration=duration,
                        token_count=result["token_count"],
                        num_rounds=len(result["chat_history"])
                    )
                    
                    # Display final answer
                    st.subheader("📝 Preparation Plan")
                    st.markdown(f"<div class='final-answer'>{result['answer']}</div>", unsafe_allow_html=True)
                    
                    # Display conversation
                    st.subheader("💬 Conversation Process")
                    display_conversation(result["chat_history"])
                    
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                    logging.exception("Error in preparation plan creation")
    
    # Tab 4: System Logs
    with tab4:
        st.header("🔧 System Logs")
        st.write("View detailed system logs for debugging.")
        
        logs_container = st.empty()
        
        # Get and display logs
        logs = get_logs()
        if logs:
            logs_container.code("\n".join(logs))
        else:
            logs_container.info("No logs available yet.")
        
        # Manual refresh button
        if st.button("Refresh Logs"):
            logs = get_logs()
            if logs:
                logs_container.code("\n".join(logs))
            else:
                logs_container.info("No logs available yet.")
        
        # Auto-refresh toggle
        auto_refresh = st.checkbox("Auto-refresh logs", value=True)
        if auto_refresh:
            st.markdown(
                """
                <script>
                    function refreshLogs() {
                        const checkbox = document.querySelector('.stCheckbox input[type="checkbox"]');
                        if (checkbox && checkbox.checked) {
                            const refreshButton = document.querySelector('button:contains("Refresh Logs")');
                            if (refreshButton) refreshButton.click();
                        }
                        setTimeout(refreshLogs, 3000);
                    }
                    setTimeout(refreshLogs, 3000);
                </script>
                """,
                unsafe_allow_html=True
            )

if __name__ == "__main__":
    try:
        logging.info("Starting Interview Preparation Assistant application")
        main()
    except Exception as e:
        st.error(f"Application error: {str(e)}")
        logging.exception("Application error")