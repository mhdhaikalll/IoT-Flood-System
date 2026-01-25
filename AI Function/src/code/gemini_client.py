"""
Gemini AI Client for Flood Detection System

This module provides integration with Google's Gemini AI for
advanced flood prediction analysis and natural language processing.
"""

import os
import httpx
import json
from typing import Optional, List, Dict, Any
from datetime import datetime

# ============== CONFIGURATION ==============

# Gemini API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

# Safety settings
SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

# Generation configuration
GENERATION_CONFIG = {
    "temperature": 0.7,
    "topK": 40,
    "topP": 0.95,
    "maxOutputTokens": 1024,
}

# ============== GEMINI CLIENT ==============

class GeminiClient:
    """Client for interacting with Google Gemini AI API"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or GEMINI_API_KEY
        self.model = GEMINI_MODEL
        self.base_url = GEMINI_API_URL
    
    async def generate_content(
        self, 
        prompt: str, 
        system_instruction: str = None,
        temperature: float = None
    ) -> Optional[str]:
        """
        Generate content using Gemini AI
        
        Args:
            prompt: The user prompt/question
            system_instruction: Optional system instruction for context
            temperature: Optional temperature override (0.0-1.0)
        
        Returns:
            Generated text response or None if failed
        """
        try:
            # Build request payload
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt}
                        ]
                    }
                ],
                "safetySettings": SAFETY_SETTINGS,
                "generationConfig": {
                    **GENERATION_CONFIG,
                    "temperature": temperature if temperature is not None else GENERATION_CONFIG["temperature"]
                }
            }
            
            # Add system instruction if provided
            if system_instruction:
                payload["systemInstruction"] = {
                    "parts": [{"text": system_instruction}]
                }
            
            # Make API request
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}?key={self.api_key}",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Extract text from response
                    candidates = data.get("candidates", [])
                    if candidates:
                        content = candidates[0].get("content", {})
                        parts = content.get("parts", [])
                        if parts:
                            return parts[0].get("text", "")
                    
                    return None
                else:
                    error_msg = response.text
                    print(f"Gemini API error ({response.status_code}): {error_msg}")
                    return None
                    
        except Exception as e:
            print(f"Gemini client error: {e}")
            return None
    
    async def analyze_flood_risk(
        self,
        water_level: float,
        rain_intensity: str,
        flood_risk: str,
        risk_percentage: float,
        historical_data: List[Dict] = None,
        warning_level: float = 50,
        danger_level: float = 80
    ) -> str:
        """
        Analyze flood risk using Gemini AI
        
        Args:
            water_level: Current water level in cm
            rain_intensity: Current rain intensity classification
            flood_risk: Current flood risk level
            risk_percentage: Calculated risk percentage
            historical_data: List of historical sensor readings
            warning_level: Warning threshold in cm
            danger_level: Danger threshold in cm
        
        Returns:
            AI-generated analysis string
        """
        # Prepare historical context
        historical_context = ""
        if historical_data and len(historical_data) > 0:
            recent_readings = historical_data[-10:]
            historical_context = f"\nRecent sensor readings (last {len(recent_readings)}):\n"
            for reading in recent_readings:
                historical_context += (
                    f"- Water: {reading.get('ultrasonic_value', 0)}cm, "
                    f"Rain: {reading.get('rain_sensor_value', 0)}%, "
                    f"Time: {reading.get('timestamp', 'N/A')}\n"
                )
        
        # Build analysis prompt
        prompt = f"""Analyze the following flood sensor data and provide a concise, actionable assessment:

CURRENT CONDITIONS:
- Water Level: {water_level} cm
- Rain Intensity: {rain_intensity}
- Flood Risk Level: {flood_risk}
- Risk Percentage: {risk_percentage:.1f}%

THRESHOLDS:
- Warning Level: {warning_level} cm
- Danger Level: {danger_level} cm
{historical_context}

Please provide:
1. A brief assessment of the current situation (1-2 sentences)
2. Predicted trend for the next 2-6 hours based on available data
3. One specific, actionable recommendation

Keep your response concise (under 150 words) and focused on practical advice.
Use clear, non-technical language suitable for general public alerts."""

        system_instruction = """You are an expert flood monitoring AI assistant. 
Your role is to analyze sensor data and provide accurate, helpful flood risk assessments.
Always prioritize public safety in your recommendations.
Be direct and avoid unnecessary jargon."""
        
        response = await self.generate_content(
            prompt=prompt,
            system_instruction=system_instruction,
            temperature=0.5  # Lower temperature for more consistent analysis
        )
        
        if response:
            return response
        else:
            return self._generate_fallback_analysis(
                water_level, rain_intensity, flood_risk, risk_percentage
            )
    
    async def generate_alert_message(
        self,
        flood_risk: str,
        risk_percentage: float,
        water_level: float,
        recommended_actions: List[str]
    ) -> str:
        """
        Generate a user-friendly alert message using Gemini
        
        Args:
            flood_risk: Current flood risk level
            risk_percentage: Calculated risk percentage
            water_level: Current water level in cm
            recommended_actions: List of recommended actions
        
        Returns:
            AI-generated alert message
        """
        actions_text = "\n".join([f"- {action}" for action in recommended_actions])
        
        prompt = f"""Create a brief, urgent alert message for the following flood situation:

Risk Level: {flood_risk.upper()}
Risk Percentage: {risk_percentage:.1f}%
Water Level: {water_level} cm

Recommended Actions:
{actions_text}

Requirements:
1. Start with an attention-grabbing statement
2. Clearly state the risk level
3. Include 2-3 most important actions
4. End with a reassuring but serious note

Keep the message under 100 words. Use emojis sparingly for emphasis."""

        response = await self.generate_content(prompt=prompt, temperature=0.3)
        
        return response or f"⚠️ FLOOD ALERT: {flood_risk.upper()} risk detected. Water level at {water_level}cm. Take immediate precautions."
    
    async def answer_question(self, question: str, context: Dict = None) -> str:
        """
        Answer a natural language question about flood conditions
        
        Args:
            question: User's question
            context: Optional context with current sensor data
        
        Returns:
            AI-generated answer
        """
        context_text = ""
        if context:
            context_text = f"""
Current System Status:
- Water Level: {context.get('water_level', 'N/A')} cm
- Rain Intensity: {context.get('rain_intensity', 'N/A')}
- Flood Risk: {context.get('flood_risk', 'N/A')}
- Risk Percentage: {context.get('risk_percentage', 'N/A')}%
"""
        
        prompt = f"""Answer the following question about flood conditions:

Question: {question}
{context_text}

Provide a helpful, accurate answer based on the context provided.
If the question cannot be answered with available information, say so politely.
Keep your response concise and informative."""

        system_instruction = """You are a helpful flood monitoring assistant.
Answer questions about flood conditions, safety, and the monitoring system.
Always prioritize accurate information and safety advice."""
        
        response = await self.generate_content(
            prompt=prompt,
            system_instruction=system_instruction
        )
        
        return response or "I'm sorry, I couldn't process your question. Please try asking in a different way."
    
    def _generate_fallback_analysis(
        self,
        water_level: float,
        rain_intensity: str,
        flood_risk: str,
        risk_percentage: float
    ) -> str:
        """Generate fallback analysis when Gemini is unavailable"""
        status = "stable" if flood_risk in ["low", "moderate"] else "concerning"
        
        if rain_intensity in ["heavy", "extreme"]:
            trend = "Water levels are expected to rise due to heavy rainfall."
        elif rain_intensity == "moderate":
            trend = "Moderate rainfall may cause gradual water level increase."
        else:
            trend = "Water levels are expected to remain stable."
        
        if flood_risk == "critical":
            action = "Immediate evacuation is strongly recommended."
        elif flood_risk == "high":
            action = "Prepare for potential evacuation and stay alert."
        else:
            action = "Continue regular monitoring."
        
        return f"Current conditions are {status} with water level at {water_level}cm. {trend} {action}"


# ============== CONVENIENCE FUNCTIONS ==============

_default_client: Optional[GeminiClient] = None

def get_gemini_client() -> GeminiClient:
    """Get or create the default Gemini client"""
    global _default_client
    if _default_client is None:
        _default_client = GeminiClient()
    return _default_client

async def analyze_with_gemini(
    water_level: float,
    rain_intensity: str,
    flood_risk: str,
    risk_percentage: float,
    historical_data: List[Dict] = None
) -> str:
    """
    Convenience function to analyze flood risk with Gemini
    
    This is the main entry point for the FastAPI backend to use.
    """
    client = get_gemini_client()
    return await client.analyze_flood_risk(
        water_level=water_level,
        rain_intensity=rain_intensity,
        flood_risk=flood_risk,
        risk_percentage=risk_percentage,
        historical_data=historical_data
    )


# ============== TESTING ==============

async def test_gemini():
    """Test Gemini integration"""
    client = GeminiClient()
    
    print("Testing Gemini AI integration...")
    
    # Test basic generation
    response = await client.generate_content("Say 'Hello, Flood Monitoring System!' in a friendly way.")
    print(f"Basic test: {response}")
    
    # Test flood analysis
    analysis = await client.analyze_flood_risk(
        water_level=65.5,
        rain_intensity="moderate",
        flood_risk="moderate",
        risk_percentage=45.0,
        historical_data=[
            {"ultrasonic_value": 60, "rain_sensor_value": 30, "timestamp": "2024-01-01T10:00:00"},
            {"ultrasonic_value": 62, "rain_sensor_value": 35, "timestamp": "2024-01-01T10:30:00"},
            {"ultrasonic_value": 65, "rain_sensor_value": 40, "timestamp": "2024-01-01T11:00:00"},
        ]
    )
    print(f"Flood analysis: {analysis}")
    
    print("Gemini integration test complete!")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_gemini())
