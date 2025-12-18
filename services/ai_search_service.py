from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from typing import List, Dict, Any
from config import settings
import logging

logger = logging.getLogger(__name__)

class AISearchService:
    """Service for retrieving documents from Azure AI Search indexes"""
    
    def __init__(self):
        self.endpoint = settings.AZURE_SEARCH_ENDPOINT
        self.key = settings.AZURE_SEARCH_KEY
        
        # Initialize search clients for both indexes
        self.internal_docs_client = SearchClient(
            endpoint=self.endpoint,
            index_name=settings.AZURE_SEARCH_INTERNAL_INDEX,
            credential=AzureKeyCredential(self.key)
        )
        
        self.historical_data_client = SearchClient(
            endpoint=self.endpoint,
            index_name=settings.AZURE_SEARCH_HISTORICAL_INDEX,
            credential=AzureKeyCredential(self.key)
        )
        
        # Field name configuration
        self.content_field = settings.AZURE_SEARCH_CONTENT_FIELD
        self.name_field = settings.AZURE_SEARCH_METADATA_NAME_FIELD
        self.path_field = settings.AZURE_SEARCH_METADATA_PATH_FIELD
        
        logger.info(f"AI Search Service initialized")
        logger.info(f"  - Internal Docs Index: {settings.AZURE_SEARCH_INTERNAL_INDEX}")
        logger.info(f"  - Historical Data Index: {settings.AZURE_SEARCH_HISTORICAL_INDEX}")
        logger.info(f"  - Content Field: {self.content_field}")
    
    def search_internal_documents(
        self, 
        query: str, 
        top: int = 5,
        filter_expr: str = None
    ) -> List[Dict[str, Any]]:
        """
        Search internal legal documents (knowledge base)
        
        Args:
            query: Search query text
            top: Number of results to return
            filter_expr: OData filter expression
            
        Returns:
            List of search results with content and metadata
        """
        logger.info("="*80)
        logger.info("SEARCHING INTERNAL DOCUMENTS")
        logger.info("="*80)
        logger.info(f"Query: {query}")
        logger.info(f"Top Results: {top}")
        logger.info(f"Filter: {filter_expr if filter_expr else 'None'}")
        
        results = []
        try:
            # Try to search with configured field names
            search_results = self.internal_docs_client.search(
                search_text=query,
                top=top,
                filter=filter_expr,
                select=[self.content_field, self.name_field, self.path_field],
                include_total_count=True
            )
            
            for idx, result in enumerate(search_results, 1):
                doc = {
                    "content": result.get(self.content_field, ""),
                    "source": result.get(self.name_field, ""),
                    "path": result.get(self.path_field, ""),
                    "score": result.get("@search.score", 0.0)
                }
                results.append(doc)
                
                logger.info(f"\n--- Result {idx} ---")
                logger.info(f"Source: {doc['source']}")
                logger.info(f"Score: {doc['score']:.4f}")
                logger.info(f"Content Preview: {doc['content'][:200]}...")
            
            logger.info(f"\nRetrieved {len(results)} internal documents")
            
        except Exception as e:
            logger.error(f"Error searching internal documents: {str(e)}")
            logger.error(f"Field configuration may be incorrect. Check your index schema.")
            logger.error(f"Expected fields: {self.content_field}, {self.name_field}, {self.path_field}")
        
        return results
    
    def search_historical_data(
        self, 
        query: str, 
        top: int = 5,
        filter_expr: str = None
    ) -> List[Dict[str, Any]]:
        """
        Search historical engagement data
        
        Args:
            query: Search query text
            top: Number of results to return
            filter_expr: OData filter expression
            
        Returns:
            List of search results with content and metadata
        """
        logger.info("="*80)
        logger.info("SEARCHING HISTORICAL DATA")
        logger.info("="*80)
        logger.info(f"Query: {query}")
        logger.info(f"Top Results: {top}")
        logger.info(f"Filter: {filter_expr if filter_expr else 'None'}")
        
        results = []
        try:
            search_results = self.historical_data_client.search(
                search_text=query,
                top=top,
                filter=filter_expr,
                select=[self.content_field, self.name_field, self.path_field],
                include_total_count=True
            )
            
            for idx, result in enumerate(search_results, 1):
                doc = {
                    "content": result.get(self.content_field, ""),
                    "source": result.get(self.name_field, ""),
                    "path": result.get(self.path_field, ""),
                    "score": result.get("@search.score", 0.0)
                }
                results.append(doc)
                
                logger.info(f"\n--- Result {idx} ---")
                logger.info(f"Source: {doc['source']}")
                logger.info(f"Score: {doc['score']:.4f}")
                logger.info(f"Content Preview: {doc['content'][:200]}...")
            
            logger.info(f"\nRetrieved {len(results)} historical documents")
            
        except Exception as e:
            logger.error(f"Error searching historical data: {str(e)}")
            logger.error(f"Field configuration may be incorrect. Check your index schema.")
            logger.error(f"Expected fields: {self.content_field}, {self.name_field}, {self.path_field}")
        
        return results
    
    def search_both_indexes(
        self, 
        query: str, 
        top_per_index: int = 3
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Search both internal and historical indexes
        
        Returns:
            Dictionary with 'internal' and 'historical' keys containing results
        """
        logger.info("\n" + "="*80)
        logger.info("COMBINED SEARCH - BOTH INDEXES")
        logger.info("="*80)
        
        internal_results = self.search_internal_documents(query, top=top_per_index)
        historical_results = self.search_historical_data(query, top=top_per_index)
        
        logger.info(f"\nCombined search complete:")
        logger.info(f"  - Internal docs: {len(internal_results)} results")
        logger.info(f"  - Historical data: {len(historical_results)} results")
        
        return {
            "internal": internal_results,
            "historical": historical_results
        }