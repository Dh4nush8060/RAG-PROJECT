"""LLM engine using Ollama llama3.1:8b for medical report explanation."""
import requests
import json
from config import OLLAMA_BASE_URL, LLM_MODEL

MEDICAL_SYSTEM_PROMPT = """You are MedExplain AI, a compassionate and knowledgeable medical report assistant. 
Your role is to help patients understand their medical lab reports in simple, everyday language.

IMPORTANT GUIDELINES:
1. Explain medical terms in simple language that a non-medical person can understand
2. Use analogies and everyday comparisons to make complex concepts clear
3. Highlight which values are normal (✅) and which need attention (⚠️)
4. NEVER diagnose or prescribe - always recommend consulting their doctor
5. Be reassuring but honest about any concerns
6. Use a warm, empathetic tone
7. Structure your response clearly with headings and bullet points
8. If values are abnormal, explain what they might mean in general terms
9. Always end with actionable next steps

FORMAT YOUR RESPONSE AS:
## 📋 Report Overview
Brief summary of what this report covers

## 🔬 Your Results Explained
Go through each test result and explain in simple terms

## ⚠️ Values That Need Attention
List any abnormal values and what they might indicate

## ✅ What's Looking Good
List normal values and what they mean for health

## 💡 Recommended Actions
Simple, actionable steps the patient can take

## 🍎 Lifestyle Tips
General health tips based on the results
"""


def generate_explanation(report_data, rag_context=""):
    """Generate a patient-friendly explanation of a medical report."""
    
    # Build the user prompt
    user_prompt = "Please explain my medical report in simple terms.\n\n"
    
    if rag_context:
        user_prompt += f"Context:\n{rag_context}\n\n"
    
    if report_data.get("test_results"):
        user_prompt += "My lab results:\n"
        for test in report_data["test_results"]:
            ref = f" (Normal range: {test['ref_low']}-{test['ref_high']})" if test.get("ref_low") is not None else ""
            user_prompt += f"- {test['name']}: {test['value']} {test['unit']}{ref} - {test['status']}\n"
    elif report_data.get("raw_text"):
        user_prompt += f"Report text:\n{report_data['raw_text'][:3000]}\n"

    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json={
                "model": LLM_MODEL,
                "messages": [
                    {"role": "system", "content": MEDICAL_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "num_predict": 2048
                }
            },
            timeout=300
        )
        response.raise_for_status()
        data = response.json()
        return data.get("message", {}).get("content", "Unable to generate explanation.")
    except requests.exceptions.Timeout:
        return "⏳ The analysis is taking longer than expected. Please try again in a moment."
    except requests.exceptions.ConnectionError:
        return "❌ Cannot connect to the AI model. Please ensure Ollama is running with llama3.1:8b model."
    except Exception as e:
        return f"❌ Error generating explanation: {str(e)}"


def chat_followup(message, conversation_history, report_context=""):
    """Handle follow-up chat questions about a report."""
    
    messages = [
        {"role": "system", "content": MEDICAL_SYSTEM_PROMPT + 
         "\n\nYou are now in a follow-up conversation. The patient has already seen their report explanation and has questions. "
         "Answer their questions clearly and simply. If they ask about something outside the report, gently redirect them to consult their doctor."
        }
    ]
    
    # Add report context as first message
    if report_context:
        messages.append({
            "role": "user",
            "content": f"[Report Context for reference - do not repeat unless asked]\n{report_context}"
        })
        messages.append({
            "role": "assistant",
            "content": "I have reviewed your report. Feel free to ask me any questions about your results!"
        })
    
    # Add conversation history
    for msg in conversation_history[-10:]:  # Keep last 10 messages for context
        messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })
    
    # Add current message
    messages.append({"role": "user", "content": message})
    
    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json={
                "model": LLM_MODEL,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "num_predict": 1024
                }
            },
            timeout=300
        )
        response.raise_for_status()
        data = response.json()
        return data.get("message", {}).get("content", "I'm sorry, I couldn't process your question.")
    except requests.exceptions.ConnectionError:
        return "❌ Cannot connect to the AI model. Please ensure Ollama is running."
    except Exception as e:
        return f"❌ Error: {str(e)}"
