from azure.cosmos import CosmosClient, PartitionKey, exceptions
from typing import Dict, Any
from config import settings

class CosmosDBClient:
    def __init__(self):
        # Validate required configuration
        if not settings.COSMOS_ENDPOINT or not settings.COSMOS_KEY:
            raise ValueError(
                "Cosmos DB configuration is missing. "
                "Please check your .env file for COSMOS_ENDPOINT and COSMOS_KEY."
            )
        
        self.client = CosmosClient(settings.COSMOS_ENDPOINT, settings.COSMOS_KEY)
        self.database = self.client.get_database_client(settings.COSMOS_DATABASE)
        
        # Initialize containers
        self.attorney_container = self._get_or_create_container(
            settings.ATTORNEY_CONTAINER,
            partition_key=PartitionKey(path="/seniority")
        )
        
        self.public_data_container = self._get_or_create_container(
            settings.PUBLIC_DATA_CONTAINER,
            partition_key=PartitionKey(path="/jurisdiction")
        )
        
        print(f"✓ Connected to Cosmos DB: {settings.COSMOS_DATABASE}")
        print(f"✓ Attorney Container: {settings.ATTORNEY_CONTAINER}")
        print(f"✓ Public Data Container: {settings.PUBLIC_DATA_CONTAINER}")
    
    def _get_or_create_container(self, container_name: str, partition_key):
        """Get existing container or create a new one"""
        try:
            container = self.database.get_container_client(container_name)
            # Test if container exists
            container.read()
            return container
        except exceptions.CosmosResourceNotFoundError:
            print(f"Creating container: {container_name}")
            return self.database.create_container(
                id=container_name,
                partition_key=partition_key
            )
    
    def insert_item(self, container_name: str, item: Dict[str, Any]):
        """Insert a new item into the specified container"""
        container = getattr(self, f"{container_name}_container")
        return container.create_item(body=item)
    
    def query_items(self, container_name: str, query: str, parameters: list = None):
        """Query items from the specified container"""
        container = getattr(self, f"{container_name}_container")
        items = container.query_items(
            query=query,
            parameters=parameters or [],
            enable_cross_partition_query=True
        )
        return list(items)
    
    def update_item(self, container_name: str, item_id: str, partition_key: str, item: Dict[str, Any]):
        """Update an existing item in the specified container"""
        container = getattr(self, f"{container_name}_container")
        return container.replace_item(item=item_id, body=item, partition_key=partition_key)
    
    def delete_item(self, container_name: str, item_id: str, partition_key: str):
        """Delete an item from the specified container"""
        container = getattr(self, f"{container_name}_container")
        container.delete_item(item=item_id, partition_key=partition_key)
    
    def get_item(self, container_name: str, item_id: str, partition_key: str):
        """Get a specific item by ID and partition key"""
        container = getattr(self, f"{container_name}_container")
        try:
            return container.read_item(item=item_id, partition_key=partition_key)
        except exceptions.CosmosResourceNotFoundError:
            return None

# Initialize the database client
db_client = CosmosDBClient()
