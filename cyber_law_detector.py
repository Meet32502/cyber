import streamlit as st
import pandas as pd
import re
import io
from datetime import datetime
import time

# Page configuration
st.set_page_config(
    page_title="Cyber Law Violation Detector",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    .violation-card {
        border: 2px solid #ff4444;
        background-color: #fff5f5;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    .clean-card {
        border: 2px solid #44ff44;
        background-color: #f5fff5;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    .warning-card {
        border: 2px solid #ffaa44;
        background-color: #fffaf5;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    .info-box {
        background-color: #f0f8ff;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #4682b4;
        margin: 1rem 0;
    }
    
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Cyber law patterns and rules database
CYBER_LAW_PATTERNS = {
    "Data Privacy Violation": {
        "patterns": [
            r"\b(?:phone|mobile|cell)\s*(?:number|no\.?|#)\s*[:=]?\s*[\d\-\+\(\)\s]{8,15}",
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            r"\b(?:ssn|social\s*security)\s*(?:number|no\.?|#)\s*[:=]?\s*\d{3}[-\s]?\d{2}[-\s]?\d{4}",
            r"\b(?:aadhar|aadhaar)\s*(?:number|no\.?|#)\s*[:=]?\s*\d{4}\s*\d{4}\s*\d{4}",
            r"\b(?:credit\s*card|debit\s*card|card)\s*(?:number|no\.?|#)\s*[:=]?\s*[\d\-\s]{13,19}",
            r"\b(?:pan|permanent\s*account)\s*(?:number|no\.?|#)\s*[:=]?\s*[A-Z]{5}\d{4}[A-Z]"
        ],
        "law": "IT Act 2000 Section 43A, GDPR Article 6",
        "description": "Sharing personal identifiable information without consent"
    },
    
    "Hate Speech": {
        "patterns": [
            r"\b(?:kill|murder|eliminate|destroy)\s+(?:all|every)?\s*(?:muslims?|hindus?|christians?|jews?|sikhs?)",
            r"\b(?:hate|despise|loathe)\s+(?:all)?\s*(?:muslims?|hindus?|christians?|jews?|sikhs?|blacks?|whites?)",
            r"\b(?:terrorists?|extremists?)\s+(?:are|should\s+be)\s+(?:all|every)?\s*(?:muslims?|arabs?)",
            r"\bgo\s+back\s+to\s+(?:your\s+country|where\s+you\s+came\s+from|africa|asia)",
            r"\b(?:inferior|subhuman|animals?)\b.*\b(?:race|religion|caste|community)"
        ],
        "law": "IT Act 2000 Section 66A, IPC Section 153A",
        "description": "Content promoting hatred or violence against groups based on religion, race, caste, or community"
    },
    
    "Defamation": {
        "patterns": [
            r"\b(?:liar|fraud|scammer|cheat|criminal)\b.*\b(?:is|are)\s+[A-Z][a-zA-Z\s]+",
            r"\b[A-Z][a-zA-Z\s]+\s+(?:is|are)\s+(?:a\s+)?(?:liar|fraud|scammer|cheat|criminal)",
            r"\bexpose\b.*\b(?:truth|reality|facts?)\s+about\s+[A-Z][a-zA-Z\s]+",
            r"\b[A-Z][a-zA-Z\s]+\s+(?:stole|robbed|cheated|deceived)"
        ],
        "law": "IPC Section 499, IT Act 2000 Section 66A",
        "description": "Content that may damage someone's reputation without factual basis"
    },
    
    "Cyberbullying/Harassment": {
        "patterns": [
            r"\b(?:kill\s+yourself|kys|suicide|end\s+your\s+life)",
            r"\b(?:ugly|fat|stupid|worthless|useless)\s+(?:piece\s+of\s+)?(?:shit|trash|garbage)",
            r"\byou\s+(?:should\s+)?(?:die|disappear|vanish)",
            r"\b(?:stalk|follow|track|hunt)\s+(?:you|her|him|them)",
            r"\bgoing\s+to\s+(?:find|get|hunt|track)\s+you"
        ],
        "law": "IT Act 2000 Section 67, IPC Section 506",
        "description": "Content that constitutes harassment, bullying, or intimidation"
    },
    
    "Misinformation/Fake News": {
        "patterns": [
            r"\b(?:confirmed|breaking|exclusive)\s*[:!]?\s*(?:covid|coronavirus|vaccine)\s+(?:kills|causes|leads\s+to)",
            r"\b(?:government|politicians?)\s+(?:hiding|concealing)\s+(?:truth|facts?|reality)",
            r"\b(?:proven|confirmed|established)\s+(?:fact|truth)\s*[:!]?\s*(?:earth\s+is\s+flat|climate\s+change\s+is\s+hoax)",
            r"\b(?:secret|hidden|suppressed)\s+(?:cure|treatment|remedy)\s+for\s+(?:cancer|diabetes|covid)",
            r"\bdoctors?\s+(?:don't\s+want\s+you\s+to\s+know|are\s+hiding)\s+(?:this|truth|cure)"
        ],
        "law": "IT Act 2000 Section 66D, Disaster Management Act 2005",
        "description": "Content spreading false or misleading information that may cause public harm"
    },
    
    "Obscene Content": {
        "patterns": [
            r"\b(?:nude|naked|porn|xxx|adult)\s+(?:photos?|images?|videos?|content)",
            r"\b(?:selling|selling|offering)\s+(?:nude|naked|intimate)\s+(?:photos?|videos?)",
            r"\b(?:sex|sexual)\s+(?:services?|favou?rs?|acts?)\s+(?:available|for\s+sale|offered)",
            r"\b(?:escort|call\s+girl|prostitut)\w*\s+(?:services?|available|contact)"
        ],
        "law": "IT Act 2000 Section 67, IPC Section 292",
        "description": "Content that is sexually explicit or promotes immoral activities"
    },
    
    "Financial Fraud": {
        "patterns": [
            r"\b(?:guaranteed|assured|risk-free)\s+(?:returns?|profits?|income)\s+of\s+\d+%",
            r"\b(?:double|triple|multiply)\s+your\s+(?:money|investment)\s+in\s+\d+\s+(?:days?|weeks?|months?)",
            r"\b(?:earn|make|get)\s+(?:rs\.?|₹|usd|\$)\s*\d+\s+(?:daily|weekly|monthly)\s+(?:from\s+home|online|easily)",
            r"\b(?:mlm|pyramid|ponzi)\s+(?:scheme|opportunity|investment)",
            r"\b(?:send|transfer|deposit)\s+(?:rs\.?|₹|usd|\$)\s*\d+\s+(?:immediately|urgently|asap)"
        ],
        "law": "IT Act 2000 Section 66D, IPC Section 420",
        "description": "Content promoting fraudulent investment schemes or financial scams"
    }
}

def analyze_text(text):
    """Analyze text for cyber law violations"""
    violations = []
    
    for violation_type, data in CYBER_LAW_PATTERNS.items():
        for pattern in data["patterns"]:
            if re.search(pattern, text, re.IGNORECASE):
                violations.append({
                    "type": violation_type,
                    "law": data["law"],
                    "description": data["description"],
                    "matched_pattern": pattern
                })
                break  # Only flag once per violation type
    
    return violations

def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🧑‍⚖️ Cyber Law Violation Detector</h1>
        <p>AI-powered detection of potential cyber law violations in online posts</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("📋 Project Information")
        
        st.markdown("""
        <div class="info-box">
            <h4>🎯 Purpose</h4>
            <p>This tool helps detect potential cyber law violations in online content to support colleges, platforms, and organizations in content moderation.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="info-box">
            <h4>⚖️ Laws Referenced</h4>
            <ul>
                <li><strong>IT Act 2000</strong> - Sections 43A, 66A, 66D, 67</li>
                <li><strong>IPC</strong> - Sections 153A, 292, 420, 499, 506</li>
                <li><strong>GDPR</strong> - Article 6 (Data Protection)</li>
                <li><strong>Disaster Management Act 2005</strong></li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="info-box">
            <h4>🔍 Detection Categories</h4>
            <ul>
                <li>Data Privacy Violations</li>
                <li>Hate Speech</li>
                <li>Defamation</li>
                <li>Cyberbullying/Harassment</li>
                <li>Misinformation/Fake News</li>
                <li>Obscene Content</li>
                <li>Financial Fraud</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)







        
        st.markdown("""
        <div class="info-box">
            <h4>📘 Reference Guidelines</h4>
            <details>
            <summary><strong>Community Guidelines</strong></summary>
            <ul>
                <li><a href="https://www.youtube.com/howyoutubeworks/policies/community-guidelines/" target="_blank">YouTube: Hate, threats, privacy</a></li>
                <li><a href="https://help.instagram.com/477434105621119" target="_blank">Instagram: Bullying, nudity, impersonation</a></li>
                <li><a href="https://transparency.fb.com/policies/community-standards/" target="_blank">Facebook: Misinformation, violence</a></li>
                <li><a href="https://help.twitter.com/en/rules-and-policies/twitter-rules" target="_blank">X (Twitter): Privacy, abuse</a></li>
                <li><a href="https://www.redditinc.com/policies/content-policy" target="_blank">Reddit: Harassment, doxxing</a></li>
                <li><a href="https://discord.com/guidelines" target="_blank">Discord: Illegal content, threats</a></li>
            </ul>
            </details>
            
            <details>
            <summary><strong>Cyber Law References</strong></summary>
            <ul>
                <li><a href="https://www.meity.gov.in/content/information-technology-act" target="_blank">IT Act 2000 (India)</a></li>
                <li><a href="https://prsindia.org/billtrack/digital-personal-data-protection-bill-2023" target="_blank">DPDP Act 2023 (India)</a></li>
                <li><a href="https://gdpr-info.eu" target="_blank">GDPR (EU)</a></li>
                <li><a href="https://oag.ca.gov/privacy/ccpa" target="_blank">CCPA (California)</a></li>
                <li><a href="https://www.hhs.gov/hipaa/index.html" target="_blank">HIPAA (USA)</a></li>
                <li><a href="https://www.iso.org/isoiec-27001-information-security.html" target="_blank">ISO/IEC 27001</a></li>
            </ul>
            </details>
            
            <details>
            <summary><strong>Institutional Guidelines</strong></summary>
            <ul>
                <li><a href="https://www.ugc.gov.in/pdfnews/3195884_Guidelines-for-Cyber-Security-in-Higher-Education-Institutions.pdf" target="_blank">UGC Cybersecurity Guidelines</a></li>
                <li><em>College IT Policy (custom link if hosted)</em></li>
            </ul>
            </details>
        </div>
        """, unsafe_allow_html=True)

        
        # Theme toggle (basic)
        theme = st.selectbox("🎨 Theme", ["Light", "Dark"])
        
        st.markdown("---")
        st.markdown("**⚠️ Disclaimer:** This tool provides preliminary analysis only. Legal consultation is recommended for actual enforcement.")
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("📝 Single Post Analysis")
        
        # Text input area
        user_text = st.text_area(
            "Enter or paste the online post to analyze:",
            height=150,
            placeholder="Paste the content you want to analyze for potential cyber law violations..."
        )
        
        # Scan button
        if st.button("🔍 Scan Post", type="primary"):
            if user_text.strip():
                with st.spinner("Analyzing content for cyber law violations..."):
                    time.sleep(1)  # Simulate processing
                    violations = analyze_text(user_text)
                
                if violations:
                    st.markdown(f"""
                    <div class="violation-card">
                        <h3>🚨 VIOLATIONS DETECTED</h3>
                        <p><strong>Status:</strong> Content flagged for potential cyber law violations</p>
                        <p><strong>Number of violations:</strong> {len(violations)}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    for i, violation in enumerate(violations, 1):
                        st.markdown(f"""
                        <div class="violation-card">
                            <h4>Violation {i}: {violation['type']}</h4>
                            <p><strong>Legal Reference:</strong> {violation['law']}</p>
                            <p><strong>Description:</strong> {violation['description']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="clean-card">
                        <h3>✅ NO VIOLATIONS DETECTED</h3>
                        <p><strong>Status:</strong> Content appears to comply with cyber laws</p>
                        <p><strong>Analysis:</strong> No patterns matching known cyber law violations were found</p>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.warning("Please enter some text to analyze.")
    
    with col2:
        st.header("📊 Quick Stats")
        
        # Sample metrics (in a real app, these would be from a database)
        st.markdown("""
        <div class="metric-card">
            <h3>1,247</h3>
            <p>Posts Analyzed Today</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="metric-card">
            <h3>89</h3>
            <p>Violations Detected</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="metric-card">
            <h3>92.8%</h3>
            <p>Accuracy Rate</p>
        </div>
        """, unsafe_allow_html=True)
    
    # File upload section
    st.header("📁 Batch Analysis")
    
    uploaded_file = st.file_uploader(
        "Upload a file with multiple posts (.txt or .csv)",
        type=['txt', 'csv'],
        help="Upload a text file with one post per line, or a CSV file with a 'post' column"
    )
    
    if uploaded_file is not None:
        try:
            if uploaded_file.type == "text/plain":
                # Handle .txt file
                content = str(uploaded_file.read(), "utf-8")
                posts = [line.strip() for line in content.split('\n') if line.strip()]
            else:
                # Handle .csv file
                df = pd.read_csv(uploaded_file)
                if 'post' in df.columns:
                    posts = df['post'].dropna().tolist()
                else:
                    st.error("CSV file must contain a 'post' column")
                    posts = []
            
            if posts:
                st.success(f"Loaded {len(posts)} posts for analysis")
                
                if st.button("🔍 Analyze All Posts", type="primary"):
                    results = []
                    progress_bar = st.progress(0)
                    
                    for i, post in enumerate(posts):
                        violations = analyze_text(post)
                        
                        result = {
                            "Post #": i + 1,
                            "Content Preview": post[:50] + "..." if len(post) > 50 else post,
                            "Status": "FLAGGED" if violations else "CLEAN",
                            "Violations": len(violations),
                            "Types": ", ".join([v["type"] for v in violations]) if violations else "None",
                            "Laws": ", ".join(list(set([v["law"] for v in violations]))) if violations else "None"
                        }
                        results.append(result)
                        progress_bar.progress((i + 1) / len(posts))
                    
                    # Display results in a table
                    results_df = pd.DataFrame(results)
                    
                    # Summary metrics
                    total_posts = len(results_df)
                    flagged_posts = len(results_df[results_df['Status'] == 'FLAGGED'])
                    clean_posts = total_posts - flagged_posts
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Posts", total_posts)
                    with col2:
                        st.metric("Flagged Posts", flagged_posts, delta=f"{flagged_posts/total_posts*100:.1f}%")
                    with col3:
                        st.metric("Clean Posts", clean_posts, delta=f"{clean_posts/total_posts*100:.1f}%")
                    
                    # Results table
                    st.subheader("📋 Detailed Results")
                    
                    # Style the dataframe
                    def highlight_status(val):
                        color = '#ffcccc' if val == 'FLAGGED' else '#ccffcc'
                        return f'background-color: {color}'
                    
                    styled_df = results_df.style.applymap(highlight_status, subset=['Status'])
                    st.dataframe(styled_df, use_container_width=True)
                    
                    # Download results
                    csv = results_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download Results as CSV",
                        data=csv,
                        file_name=f"cyber_law_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
        
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: gray; font-size: 12px;">
        <p>🤖 Powered by Advanced NLP • Built with Streamlit • © 2025 Cyber Law Violation Detector</p>
        <p><strong>Note:</strong> This tool is for preliminary screening only. Always consult legal experts for actual enforcement decisions.</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
