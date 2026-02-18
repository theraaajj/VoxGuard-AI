#!/bin/bash

# 1. Start the Background Monitor (Silently)
# The '&' sends it to the background so the script continues
python -m components.monitor &

# 2. Start the Streamlit Dashboard
# Render provides the PORT variable automatically
streamlit run dashboard.py --server.port $PORT --server.address 0.0.0.0