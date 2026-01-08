#!/usr/bin/env python3
"""
Test script to list available Gemini models and test API connection
"""
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

# Get API key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("❌ GEMINI_API_KEY not found in .env file")
    exit(1)

print(f"✅ API Key found: {api_key[:10]}...")

# Configure Gemini
genai.configure(api_key=api_key)

print("\n📋 Listing available models that support generateContent:\n")

try:
    # List all available models
    for model in genai.list_models():
        if 'generateContent' in model.supported_generation_methods:
            print(f"✓ {model.name}")
            print(f"  Description: {model.description}")
            print(f"  Input limit: {model.input_token_limit} tokens")
            print(f"  Output limit: {model.output_token_limit} tokens")
            print()

    print("\n🧪 Testing a simple generation with models/gemini-2.5-flash...")
    model = genai.GenerativeModel('models/gemini-2.5-flash')
    response = model.generate_content("Say hello in one word")
    print(f"✅ Success! Response: {response.text}")

except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\nTry these alternatives:")
    print("1. Use 'models/gemini-1.5-pro' instead")
    print("2. Use 'models/gemini-2.0-flash-exp'")
    print("3. Generate a new API key at https://aistudio.google.com/app/apikey")
