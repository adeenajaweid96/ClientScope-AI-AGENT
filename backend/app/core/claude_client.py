"""Claude API client wrapper for vision and structured output"""

import base64
from pathlib import Path
from typing import Any, Optional, Dict
import json
import time

from anthropic import Anthropic
from pydantic import BaseModel

from app.core.config import settings


class ClaudeClient:
    """Wrapper for Anthropic Claude API with vision and tool use support"""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Claude client

        Args:
            api_key: Anthropic API key (defaults to settings.ANTHROPIC_API_KEY)
        """
        self.client = Anthropic(api_key=api_key or settings.ANTHROPIC_API_KEY)
        self.model = "claude-sonnet-4-20250514"  # Latest Claude Sonnet with vision

    def extract_text_from_image(
        self,
        image_path: str,
        prompt: str = "Extract all text from this image. Preserve formatting and structure."
    ) -> str:
        """Extract text from an image using Claude vision

        Args:
            image_path: Path to image file
            prompt: Instruction prompt for extraction

        Returns:
            Extracted text content
        """
        # Read and encode image
        image_data = Path(image_path).read_bytes()
        base64_image = base64.standard_b64encode(image_data).decode("utf-8")

        # Detect media type
        suffix = Path(image_path).suffix.lower()
        media_type_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp"
        }
        media_type = media_type_map.get(suffix, "image/jpeg")

        # Call Claude with vision
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": base64_image,
                            },
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ],
                }
            ],
        )

        return response.content[0].text

    def _normalize_data(self, data: Any) -> Any:
        """Recursively normalize data from Claude responses

        Handles:
        - severity fields to lowercase
        - risk_description -> description field name mapping

        Args:
            data: Data structure (dict, list, or primitive)

        Returns:
            Normalized data
        """
        if isinstance(data, dict):
            normalized = {}
            for key, value in data.items():
                # Normalize severity to lowercase
                if key == "severity" and isinstance(value, str):
                    normalized[key] = value.lower()
                # Map risk_description to description
                elif key == "risk_description":
                    normalized["description"] = value
                else:
                    normalized[key] = self._normalize_data(value)
            return normalized
        elif isinstance(data, list):
            return [self._normalize_data(item) for item in data]
        else:
            return data

    def structured_output(
        self,
        prompt: str,
        schema: type[BaseModel],
        system_prompt: Optional[str] = None,
        max_retries: int = 2
    ) -> BaseModel:
        """Get structured output using Claude tool use with retry logic

        Args:
            prompt: User prompt
            schema: Pydantic model defining the output structure
            system_prompt: Optional system prompt
            max_retries: Number of retry attempts if tool use fails

        Returns:
            Instance of the schema model with extracted data
        """
        # Convert Pydantic model to tool schema
        json_schema = schema.model_json_schema()

        # Clean up schema for Anthropic API and add field descriptions
        properties = json_schema.get("properties", {})

        # Simplify schema to avoid Claude inventing field names
        tool_input_schema = {
            "type": "object",
            "properties": properties,
            "required": json_schema.get("required", [])
        }

        tool_schema = {
            "name": "extract_structured_data",
            "description": f"Extract structured data conforming to {schema.__name__} schema. Use EXACT field names from the schema.",
            "input_schema": tool_input_schema
        }

        messages = [{"role": "user", "content": prompt}]

        last_error = None

        for attempt in range(max_retries + 1):
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    system=system_prompt or "Extract structured information from the input. Use the EXACT field names from the provided schema. Do not engage in conversation - only extract data using the tool.",
                    messages=messages,
                    tools=[tool_schema],
                    tool_choice={"type": "tool", "name": "extract_structured_data"}
                )

                # Extract tool use result
                for block in response.content:
                    if block.type == "tool_use" and block.name == "extract_structured_data":
                        # Normalize data before validation
                        normalized_data = self._normalize_data(block.input)
                        return schema.model_validate(normalized_data)

                # If no tool use found but we have text, this might be a conversation response
                if response.content and response.content[0].type == "text":
                    text_response = response.content[0].text

                    # On retry, add a stronger directive
                    if attempt < max_retries:
                        messages.append({
                            "role": "assistant",
                            "content": text_response
                        })
                        messages.append({
                            "role": "user",
                            "content": "Please use the extract_structured_data tool to provide the response in the required structured format. Do not provide a text explanation - use the tool."
                        })
                        time.sleep(0.5)  # Brief delay before retry
                        continue

                    # On last attempt, try to parse JSON from text
                    try:
                        json_start = text_response.find("{")
                        json_end = text_response.rfind("}") + 1
                        if json_start >= 0 and json_end > json_start:
                            json_str = text_response[json_start:json_end]
                            data = json.loads(json_str)
                            normalized_data = self._normalize_data(data)
                            return schema.model_validate(normalized_data)
                    except (json.JSONDecodeError, ValueError):
                        pass

                last_error = f"No tool use found in response. Response type: {response.content[0].type if response.content else 'empty'}"

            except Exception as e:
                last_error = str(e)
                if attempt < max_retries:
                    time.sleep(1)  # Wait before retry
                    continue

        raise ValueError(f"Failed to get structured output after {max_retries + 1} attempts. Last error: {last_error}")


# Global client instance
_client: Optional[ClaudeClient] = None


def get_claude_client() -> ClaudeClient:
    """Get or create global Claude client instance"""
    global _client
    if _client is None:
        _client = ClaudeClient()
    return _client
