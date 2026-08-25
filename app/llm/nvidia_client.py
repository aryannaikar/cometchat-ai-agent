import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


class NVIDIAClient:
    """Client for NVIDIA's OpenAI-compatible API."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "meta/llama-3.1-8b-instruct",
    ):
        self.api_key = api_key or os.getenv("NVIDIA_API_KEY")

        if not self.api_key:
            raise ValueError(
                "NVIDIA_API_KEY environment variable is not set."
            )

        self.model = model

        self.client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=self.api_key,
        )

    def generate(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            temperature=0,
        )

        return response.choices[0].message.content.strip()