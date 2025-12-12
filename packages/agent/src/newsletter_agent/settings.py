"""Settings module for centralized secret and configuration management."""

import os
from typing import Optional
from pydantic import BaseModel, Field


class OpenAISettings(BaseModel):
    """Azure OpenAI configuration settings."""
    endpoint: str
    api_key: str
    api_version: str = "2024-10-21"
    deployment: str = "gpt-4o-mini"
    temperature: float = 0.2
    timeout: int = 45


class FoundrySettings(BaseModel):
    """Foundry grounding service configuration settings."""
    project_endpoint: str
    bing_connection_id: str


class EmailSettings(BaseModel):
    """
    Email service configuration settings.
    
    SECURITY NOTE - Least Privilege Access:
    The email API key should have ONLY the following permissions:
    - SEND email permission (no read, delete, or admin permissions)
    - Rate limiting configured at the API level
    - Sender email address restricted to newsletter domain
    
    Implementation steps:
    1. Use a dedicated email service API key for newsletter sending only
    2. Configure sender policy framework (SPF) and DKIM
    3. Implement rate limiting (e.g., max 1000 emails/hour)
    4. Monitor for abuse and implement anomaly detection
    """
    # TODO: Add email-specific settings when email service is implemented
    # api_key: str  # Should have send-only permissions
    # sender_email: str
    # sender_name: str
    # max_send_rate: int = 1000  # emails per hour
    pass


class ExternalAPISettings(BaseModel):
    """External API keys for news sources."""
    nyt_api_key: Optional[str] = None
    x_bearer_token: Optional[str] = None


class DatabaseSettings(BaseModel):
    """
    Database connection settings.
    
    SECURITY NOTE - Least Privilege Access:
    In production, the newsletter agent should use a Cosmos DB connection
    with the following scoped permissions:
    - READ access to: Subscriptions container (to fetch user subscriptions)
    - WRITE access to: Newsletters container (to store generated newsletters)
    - NO access to: User data, payment info, or other sensitive containers
    
    Implementation steps for Azure:
    1. Create a separate Azure AD service principal for the newsletter agent
    2. Assign Cosmos DB Data Contributor role scoped to specific containers
    3. Use Managed Identity for authentication (preferred) or SAS tokens
    4. Rotate keys regularly (every 90 days minimum)
    """
    # TODO: Add Cosmos DB connection settings with least-privilege keys
    # cosmos_endpoint: str
    # cosmos_key: str  # Should be read/write scoped to newsletters container only
    # cosmos_database: str
    # subscriptions_container: str  # Read-only access
    # newsletters_container: str    # Read/write access
    pass


def get_openai_settings() -> OpenAISettings:
    """
    Get Azure OpenAI settings from environment variables.
    
    Returns:
        OpenAISettings object with Azure OpenAI configuration
    
    Raises:
        ValueError: If required environment variables are not set
    """
    endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    api_key = os.environ.get("AZURE_OPENAI_API_KEY")
    
    if not endpoint or not api_key:
        raise ValueError(
            "Azure OpenAI configuration missing. "
            "Please set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY environment variables."
        )
    
    return OpenAISettings(
        endpoint=endpoint,
        api_key=api_key,
        api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-10-21"),
        deployment=os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini"),
    )


def get_foundry_settings() -> Optional[FoundrySettings]:
    """
    Get Foundry settings from environment variables.
    
    Returns:
        FoundrySettings object if configured, None otherwise
    """
    endpoint = os.environ.get("FOUNDRY_PROJECT_ENDPOINT")
    connection_id = os.environ.get("FOUNDRY_BING_CONNECTION_ID")
    
    if not endpoint or not connection_id:
        return None
    
    return FoundrySettings(
        project_endpoint=endpoint,
        bing_connection_id=connection_id,
    )


def get_external_api_settings() -> ExternalAPISettings:
    """
    Get external API settings from environment variables.
    
    Returns:
        ExternalAPISettings object with available API keys
    """
    return ExternalAPISettings(
        nyt_api_key=os.environ.get("NYT_API_KEY"),
        x_bearer_token=os.environ.get("X_BEARER_TOKEN"),
    )


def get_email_settings() -> EmailSettings:
    """
    Get email service settings from environment variables.
    
    Returns:
        EmailSettings object
    
    Note:
        TODO: Implement email settings when email service is added
    """
    return EmailSettings()


def get_database_settings() -> DatabaseSettings:
    """
    Get database connection settings from environment variables.
    
    Returns:
        DatabaseSettings object
    
    Note:
        TODO: Implement database settings for Cosmos DB
        These should use least-privilege keys (read/write only for newsletter agent)
    """
    return DatabaseSettings()
