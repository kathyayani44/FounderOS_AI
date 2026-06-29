import os
import logging
from typing import Type, TypeVar, Optional
from pydantic import BaseModel
from backend.app.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gemini_client")

T = TypeVar("T", bound=BaseModel)

# Try importing the new google-genai SDK
try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    logger.warning("google-genai SDK not importable. Falling back to simulation mode.")
    GENAI_AVAILABLE = False

def get_gemini_client():
    if not GENAI_AVAILABLE:
        return None
    
    api_key = os.getenv("GEMINI_API_KEY") or settings.GEMINI_API_KEY
    if not api_key:
        logger.warning("GEMINI_API_KEY is not set. Agents will run in SIMULATION/MOCK mode.")
        return None
    
    try:
        return genai.Client(api_key=api_key)
    except Exception as e:
        logger.error(f"Error initializing Gemini client: {e}. Falling back to MOCK mode.")
        return None

def generate_structured_output(
    prompt: str,
    response_schema: Type[T],
    system_instruction: Optional[str] = None,
    mock_fallback_data: Optional[T] = None
) -> T:
    """
    Sends a structured generation prompt to Gemini 2.5 Flash.
    Enforces the return format using the provided Pydantic response_schema.
    If the API key is missing or an error occurs, falls back to mock_fallback_data.
    """
    client = get_gemini_client()
    
    if not client:
        if mock_fallback_data is not None:
            logger.info("Running in SIMULATION mode: returned pre-defined Pydantic fallback data.")
            return mock_fallback_data
        raise ValueError("Gemini client is not initialized and no mock fallback data was provided.")

    try:
        # Prepare the generate config with schema validation
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=response_schema,
            system_instruction=system_instruction,
            temperature=0.2,
        )
        
        logger.info("Invoking Gemini 2.5 Flash for structured output...")
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=config
        )
        
        if not response.text:
            raise ValueError("Received empty text response from Gemini API.")
            
        logger.info("Successfully received structured response from Gemini API.")
        return response_schema.model_validate_json(response.text)
        
    except Exception as e:
        logger.error(f"Gemini API or validation error: {e}.")
        if mock_fallback_data is not None:
            logger.info("Falling back to SIMULATION mode due to API error.")
            return mock_fallback_data
        raise e
