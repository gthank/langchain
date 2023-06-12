"""Wrapper around OctoAI APIs."""
from typing import Any, Dict, List, Mapping, Optional
from pydantic import Extra, root_validator

from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain.llms.base import LLM
from langchain.llms.utils import enforce_stop_tokens
from langchain.utils import get_from_dict_or_env

from octoai import client


class OctoAIEndpoint(LLM):
    """Wrapper around OctoAI Inference Endpoints.
    OctoAIEndpoint is a class to interact with OctoAI Compute Service large language model endpoints.

    To use, you should have the ``octoai`` python package installed, and the
    environment variable ``OCTOAI_API_TOKEN`` set with your API token, or pass
    it as a named parameter to the constructor.

    Example:
        .. code-block:: python

            from langchain.llms.octoai_endpoint  import OctoAIEndpoint
            OctoAIEndpoint(
                octoai_api_token="octoai-api-key",                
                endpoint_url="https://mpt-7b-demo-kk0powt97tmb.octoai.cloud/generate",
                model_kwargs={
                    "max_new_tokens": 200,
                    "temperature": 0.75,
                    "top_p": 0.95,
                    "repetition_penalty": 1,
                    "seed": None,
                    "stop": [],
                },
            )
            
    """

    endpoint_url: Optional[str] = None
    """Endpoint URL to use."""

    model_kwargs: Optional[dict] = None
    """Key word arguments to pass to the model."""

    octoai_api_token: Optional[str] = None
    """OCTOAI API Token"""

    class Config:
        """Configuration for this pydantic object."""

        extra = Extra.forbid

    @root_validator(allow_reuse=True)
    def validate_environment(cls, values: Dict) -> Dict:
        """Validate that api key and python package exists in environment."""
        octoai_api_token = get_from_dict_or_env(
            values, "octoai_api_token", "OCTOAI_API_TOKEN"
        )
        values["endpoint_url"] = get_from_dict_or_env(
            values, "endpoint_url", "ENDPOINT_URL"
        )

        values["octoai_api_token"] = octoai_api_token
        return values

    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        """Get the identifying parameters."""
        _model_kwargs = self.model_kwargs or {}
        return {
            **{"endpoint_url": self.endpoint_url},
            **{"model_kwargs": _model_kwargs},
        }

    @property
    def _llm_type(self) -> str:
        """Return type of llm."""
        return "octoai_endpoint"

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
    ) -> str:
        """Call out to OctoAI's inference endpoint.

        Args:
            prompt: The prompt to pass into the model.
            stop: Optional list of stop words to use when generating.

        Returns:
            The string generated by the model.

        """
        _model_kwargs = self.model_kwargs or {}

        # Prepare the payload JSON
        parameter_payload = {"inputs": prompt, "parameters": _model_kwargs}

        try:
            # Initialize the OctoAI client            
            octoai_client = client.Client(token=self.octoai_api_token)
            
            # Send the request using the OctoAI client            
            resp_json = octoai_client.infer(self.endpoint_url, parameter_payload)
            text = resp_json["generated_text"]

        except Exception as e:
            # Handle any errors raised by the inference endpoint        
            raise ValueError(f"Error raised by the inference endpoint: {e}") from e

        if stop is not None:
            # Apply stop tokens when making calls to OctoAI
            text = enforce_stop_tokens(text, stop)

        return text
