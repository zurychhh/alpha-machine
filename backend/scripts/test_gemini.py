#!/usr/bin/env python3
"""Test Gemini API connection"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()


def test_gemini():
    api_key = os.getenv("GOOGLE_AI_API_KEY")

    if not api_key:
        print("GOOGLE_AI_API_KEY not found in .env")
        return False

    print(f"API Key found: {api_key[:20]}...")

    try:
        genai.configure(api_key=api_key)

        # Test with gemini-2.0-flash model
        model = genai.GenerativeModel("gemini-2.0-flash")

        print("Testing Gemini API with gemini-2.0-flash...")
        response = model.generate_content("Say hello in one sentence")

        print(f"GEMINI WORKS!")
        print(f"Response: {response.text}")
        return True

    except Exception as e:
        print(f"Gemini error: {e}")

        if "429" in str(e):
            print("429 error - quota issue")
            print("Solution: Wait for billing to activate or check quota")
        elif "404" in str(e):
            print("404 error - model not found")
            print("Try different model: gemini-pro, gemini-1.5-flash, gemini-2.0-flash")

        return False


if __name__ == "__main__":
    success = test_gemini()
    sys.exit(0 if success else 1)
