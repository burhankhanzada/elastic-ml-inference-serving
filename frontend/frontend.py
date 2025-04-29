import streamlit as st
import requests

# Set page configuration
st.set_page_config(
    page_title="Elastic ML Inferencing",
    page_icon="🤖",
    layout="wide"
)

# Custom CSS to enhance aesthetic
st.markdown("""
<style>
    .main-header {
        font-size: 36px;
        font-weight: bold;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 20px;
    }
    .sub-header {
        font-size: 24px;
        font-weight: bold;
        color: #0D47A1;
        margin-top: 20px;
        margin-bottom: 10px;
    }
    .team-section {
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 20px;
    }
    .team-member {
        text-align: center;
        padding: 10px;
        border-radius: 5px;
        background-color: #f5f5f5;
        height: 100%;
    }
    .project-card {
        background-color: #f9f9f9;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

def predict(uploaded_image):
    """
    This function reads the uploaded image and passes it to the requests.post() method
    that hits the backend FastAPI service (/predict) to use the ResNet18 model for inferecing.
    """
    try:
        file = {'image': uploaded_image}
        response = requests.post(API_URL, files=file)
        st.success(f"Prediction: {response.json()['prediction']}")
        return response.json()['prediction']
    except Exception as e:
        st.error(f"Error during prediction: {str(e)}")
        return None

API_URL = 'http://127.0.0.1:8000/predict'

# --------- Sidebar Content ---------
st.sidebar.markdown('<div class="sub-header">Project Overview</div>', unsafe_allow_html=True)

with st.sidebar:
    with st.expander("About This Project", expanded=True):
        st.markdown("""
        This project implements an autoscaling system for image classification in a Kubernetes environment. 
        We compare custom autoscaling strategies with Kubernetes' native Horizontal Pod Autoscaler (HPA).
        
        The system features:
        - Fast inference with ResNet18 model
        - Smart request dispatching
        - Custom autoscaling algorithm
        - Real-time performance monitoring
        
        Our goal is to achieve sub-0.5s latency while optimizing resource usage.
        """)
    
    st.markdown('<div class="sub-header">Team Members</div>', unsafe_allow_html=True)
    
    # Team members section with columns for better layout
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.image("https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973460_960_720.png", width=80)
        st.markdown("**Muhammad Ozair**")
    
    with col2:
        st.image("https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973460_960_720.png", width=80)
        st.markdown("**Kamil Hassaan**")
    
    with col3:
        st.image("https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973460_960_720.png", width=80)
        st.markdown("**Umair Hussain**")
    
    with st.expander("Technical Details"):
        st.markdown("""
        - **Architecture**: Kubernetes-based microservices
        - **ML Model**: ResNet18 (CPU-only)
        - **Target Latency**: <0.5s (99th percentile)
        - **Custom Autoscaler**: 15-second decision interval
        - **Evaluation**: Custom vs. HPA (70% & 90% CPU)
        """)

# --------- Main Content ---------
st.markdown('<div class="main-header">Elastic ML Inferencing 🚀</div>', unsafe_allow_html=True)

# Project introduction card
with st.container():
    st.markdown("""
    <div class="project-card">
        <h2>Welcome to our ML Autoscaling Demo</h2>
        <p>This application demonstrates intelligent autoscaling for machine learning inference. 
        Upload an image to classify it using our ResNet18 model deployed in Kubernetes with custom autoscaling.</p>
        <p>Our system optimizes resource usage while maintaining low latency, even under variable load conditions.</p>
    </div>
    """, unsafe_allow_html=True)

# Main functionality
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown('<div class="sub-header">Test the Model</div>', unsafe_allow_html=True)
    image = st.file_uploader(label='Upload an image to classify:', type=['jpg', 'jpeg', 'png'])
    
    if image:
        predict_button = st.button("🔍 Classify Image", use_container_width=True)

with col2:
    st.markdown('<div class="sub-header">Image Preview</div>', unsafe_allow_html=True)
    if image:
        st.image(image, width=300)
        if predict_button:
            with st.spinner("Classifying..."):
                prediction = predict(image)
                
# Performance metrics visualization placeholder
if st.checkbox("Show System Performance"):
    st.markdown('<div class="sub-header">System Performance</div>', unsafe_allow_html=True)
    
    metrics_tab1, metrics_tab2 = st.tabs(["Latency", "Resource Usage"])
    
    with metrics_tab1:
        st.markdown("#### 99th Percentile Latency")
        st.line_chart({"Custom Autoscaler": [0.3, 0.32, 0.29, 0.35, 0.4, 0.38], 
                       "HPA (70% CPU)": [0.42, 0.45, 0.43, 0.47, 0.51, 0.48],
                       "HPA (90% CPU)": [0.47, 0.49, 0.52, 0.55, 0.51, 0.53]})
    
    with metrics_tab2:
        st.markdown("#### CPU Cores Utilization")
        st.line_chart({"Custom Autoscaler": [2, 3, 4, 5, 6, 5], 
                       "HPA (70% CPU)": [2, 2, 3, 4, 5, 5],
                       "HPA (90% CPU)": [1, 2, 2, 3, 4, 3]})

# Footer
st.markdown("---")
st.markdown("*Cloud Computing Advanced Practical Lab - 2025*")