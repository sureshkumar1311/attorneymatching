from datetime import datetime, timedelta
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from config import settings

# Get configuration from settings
AZURE_STORAGE_CONNECTION_STRING = settings.AZURE_STORAGE_CONNECTION_STRING
BLOB_INTERNAL_CONTAINER = settings.BLOB_INTERNAL_CONTAINER
BLOB_ATTORNEY_HISTORY_CONTAINER = settings.BLOB_ATTORNEY_HISTORY_CONTAINER

# Validate required configuration
if not AZURE_STORAGE_CONNECTION_STRING:
    raise ValueError(
        "AZURE_STORAGE_CONNECTION_STRING is not set. "
        "Please check your .env file and ensure it contains the connection string."
    )

if not BLOB_INTERNAL_CONTAINER or not BLOB_ATTORNEY_HISTORY_CONTAINER:
    raise ValueError(
        "Blob container names are not set. "
        "Please check your .env file for BLOB_INTERNAL_CONTAINER and BLOB_ATTORNEY_HISTORY_CONTAINER."
    )

# Initialize blob service client
blob_service_client = BlobServiceClient.from_connection_string(
    AZURE_STORAGE_CONNECTION_STRING
)

# Get container clients
internal_container = blob_service_client.get_container_client(
    BLOB_INTERNAL_CONTAINER
)

attorney_history_container = blob_service_client.get_container_client(
    BLOB_ATTORNEY_HISTORY_CONTAINER
)

# Ensure containers exist
for container in [internal_container, attorney_history_container]:
    try:
        container.create_container()
        print(f"Container '{container.container_name}' created successfully.")
    except Exception as e:
        # Container might already exist, which is fine
        if "ContainerAlreadyExists" in str(e):
            print(f"Container '{container.container_name}' already exists.")
        else:
            print(f"Note: {str(e)}")


def generate_sas_url(container_client, blob_name, expiry_minutes=10):
    """
    Generate a SAS URL for a blob with read permissions.
    
    Args:
        container_client: Azure blob container client
        blob_name: Name of the blob
        expiry_minutes: How long the SAS URL should be valid (default: 10 minutes)
    
    Returns:
        str: Complete URL with SAS token
    """
    account_name = container_client.account_name
    container_name = container_client.container_name
    account_key = container_client.credential.account_key

    sas_token = generate_blob_sas(
        account_name=account_name,
        container_name=container_name,
        blob_name=blob_name,
        account_key=account_key,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.utcnow() + timedelta(minutes=expiry_minutes)
    )

    url = f"https://{account_name}.blob.core.windows.net/{container_name}/{blob_name}?{sas_token}"
    return url
