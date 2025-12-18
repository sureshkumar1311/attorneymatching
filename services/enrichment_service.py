import aiohttp
from typing import Dict, Any, Tuple
from services.public_source_service import PublicSourceService
from config import settings

class EnrichmentService:
    def __init__(self):
        self.public_source_service = PublicSourceService()
    
    @staticmethod
    async def fetch_url_content(url: str, timeout: int = 30) -> str:
        """Fetch content from URL"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=timeout) as response:
                    if response.status == 200:
                        return await response.text()
                    else:
                        raise Exception(f"HTTP {response.status}")
        except Exception as e:
            raise Exception(f"Failed to fetch URL: {str(e)}")
    
    @staticmethod
    async def enrich_with_llm(title: str, content: str, url: str) -> Dict[str, Any]:
        """
        Call OpenAI/Claude API to enrich content
        TODO: Implement actual LLM API call
        
        Example prompt for GPT-4 or Claude:
        
        Analyze this legal news article and extract the following information in JSON format:
        
        1. risk_area: Choose from (Data Protection, Corporate Governance, Securities Law, Tax, 
           Employment, Intellectual Property, Antitrust, Banking, Insurance, Real Estate, 
           Environmental, Healthcare)
        2. summary: Provide a 2-3 sentence summary
        3. relevant_topics: List 3-5 relevant keywords
        4. jurisdiction: Country or region (e.g., "United States", "European Union", "Global")
        5. impact_level: Choose from (Low, Medium, High)
        6. source: Name of the publishing organization
        
        Article Title: {title}
        Article URL: {url}
        Article Content: {content[:5000]}
        
        Return ONLY valid JSON with these exact keys.
        """
        
        # TODO: Implement actual OpenAI/Claude API call
        # For now, return mock data
        return {
            "risk_area": "Data Protection",
            "summary": f"Analysis of: {title}",
            "relevant_topics": ["Legal", "Compliance", "Regulation"],
            "jurisdiction": "United States",
            "impact_level": "Medium",
            "source": "Legal News Source"
        }
    
    async def enrich_public_source(self, news_id: str) -> Tuple[bool, str]:
        """Full enrichment pipeline for a public source"""
        
        try:
            # Get the source
            source = self.public_source_service.get_public_source_by_id(news_id)
            if not source:
                return False, f"News item {news_id} not found"
            
            # Check retry limit
            if source.get('enrichment_retry_count', 0) >= settings.MAX_ENRICHMENT_RETRIES:
                return False, "Max retry attempts reached"
            
            # Update status to processing
            self.public_source_service.update_enrichment_status(news_id, 'processing')
            
            # Fetch content
            url = source['reference']['url']
            title = source['title']
            content = await self.fetch_url_content(url)
            
            # Enrich with LLM
            enriched_data = await self.enrich_with_llm(title, content, url)
            
            # Prepare update data
            update_data = {
                'risk_area': enriched_data.get('risk_area'),
                'summary': enriched_data.get('summary'),
                'relevant_topics': enriched_data.get('relevant_topics', []),
                'jurisdiction': enriched_data.get('jurisdiction', 'Unknown'),
                'impact_level': enriched_data.get('impact_level'),
                'reference': {
                    'source': enriched_data.get('source'),
                    'url': url,
                    'published_date': enriched_data.get('published_date')
                }
            }
            
            # Update with completed status
            self.public_source_service.update_enrichment_status(
                news_id,
                'completed',
                update_data
            )
            
            return True, "Enrichment successful"
            
        except Exception as e:
            # Update to failed status
            self.public_source_service.update_enrichment_status(news_id, 'failed')
            return False, f"Enrichment failed: {str(e)}"
