from azure.cosmos import CosmosClient, PartitionKey, exceptions
from typing import Dict, Any, List
from config import settings

class DatabaseService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
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
        
        self._initialized = True
    
    def _get_or_create_container(self, container_name: str, partition_key):
        """Get existing container or create new one"""
        try:
            return self.database.get_container_client(container_name)
        except exceptions.CosmosResourceNotFoundError:
            return self.database.create_container(
                id=container_name,
                partition_key=partition_key
            )
    
    def insert_item(self, container_name: str, item: Dict[str, Any]) -> Dict[str, Any]:
        """Insert item into container"""
        container = self._get_container(container_name)
        return container.create_item(body=item)
    
    def query_items(self, container_name: str, query: str, parameters: List = None) -> List[Dict[str, Any]]:
        """Query items from container"""
        container = self._get_container(container_name)
        items = container.query_items(
            query=query,
            parameters=parameters or [],
            enable_cross_partition_query=True
        )
        return list(items)
    
    def update_item(self, container_name: str, item_id: str, partition_key: str, item: Dict[str, Any]) -> Dict[str, Any]:
        """Update item in container"""
        container = self._get_container(container_name)
        return container.replace_item(item=item_id, body=item, partition_key=partition_key)
    
    def delete_item(self, container_name: str, item_id: str, partition_key: str):
        """Delete item from container"""
        container = self._get_container(container_name)
        container.delete_item(item=item_id, partition_key=partition_key)
    
    def _get_container(self, container_name: str):
        """Get container client by name"""
        if container_name == settings.ATTORNEY_CONTAINER:
            return self.attorney_container
        elif container_name == settings.PUBLIC_DATA_CONTAINER:
            return self.public_data_container
        else:
            raise ValueError(f"Unknown container: {container_name}")
