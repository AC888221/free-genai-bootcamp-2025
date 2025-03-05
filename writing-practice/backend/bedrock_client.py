# bedrock_client.py (added back)

import boto3
import streamlit as st
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@st.cache(hash_funcs={boto3.client: lambda _: None})
def get_bedrock_client():
    try:
        bedrock_runtime = boto3.client(
            service_name="bedrock-runtime",
            region_name="us-east-1",  # Change to your region
        )
        return bedrock_runtime
    except Exception as e:
        logger.error(f"Error creating Bedrock client: {e}")
        st.error("Failed to create Bedrock client. Please check your AWS configuration.")
        return None