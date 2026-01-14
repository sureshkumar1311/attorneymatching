from openai import AzureOpenAI
from typing import List, Dict, Any, Tuple
import json
import logging
from config import settings
from services.ai_search_service import AISearchService
from services.public_source_service import PublicSourceService
from services.attorney_service import AttorneyService
from risk_analysis_model import (
    RiskAnalysisRequest, 
    RiskAnalysisResponse, 
    ReferenceItem,
    RecommendedAttorney
)

logger = logging.getLogger(__name__)

class RiskAnalysisService:
    """Service for performing RAG-based risk analysis and attorney matching"""
    
    def __init__(self):
        self.ai_search = AISearchService()
        self.public_source_service = PublicSourceService()
        self.attorney_service = AttorneyService()
        
        # Initialize Azure OpenAI client
        self.llm_client = AzureOpenAI(
            api_key=settings.AZURE_OPENAI_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
        )
        
        logger.info("Risk Analysis Service initialized")
    
    def analyze_company_risks(self, request: RiskAnalysisRequest) -> RiskAnalysisResponse:
        """
        Main method to analyze company risks and recommend attorney
        
        Pipeline:
        1. Search internal legal documents for practice area knowledge
        2. Search historical engagements for similar cases
        3. Query public data sources for recent risks
        4. Build context and prompt for LLM
        5. Get risk analysis from LLM
        6. Match attorney based on practice area and experience
        7. Generate email template
        8. Return structured response
        """
        logger.info("\n" + "="*80)
        logger.info("STARTING RISK ANALYSIS PIPELINE")
        logger.info("="*80)
        logger.info(f"Company: {request.companyName}")
        logger.info(f"Practice Area: {request.practicearea}")
        logger.info(f"Email: {request.companyemail}")
        logger.info(f"Phone: {request.companyphonenumber}")
        
        # Step 1: Retrieve relevant documents using RAG
        rag_context = self._retrieve_rag_context(request)
        
        # Step 2: Get public data sources for additional context
        public_sources = self._get_relevant_public_sources(request.practicearea)
        
        # Step 3: Build LLM prompt with context
        prompt = self._build_risk_analysis_prompt(request, rag_context, public_sources)
        
        # Step 4: Get risk analysis from LLM
        risks, references, confidence = self._get_llm_risk_analysis(prompt, public_sources)
        
        # Step 5: Find best matching attorney
        attorneys = self._find_matching_attorneys(request.practicearea, rag_context)
        
        # Step 6: Generate email template
        email_template = self._generate_email_template(
            request, 
            attorneys[0], 
            risks
        )
        
        # Step 7: Build response
        response = RiskAnalysisResponse(
            company=request.companyName,
            practice_area=request.practicearea,
            risks=risks,
            references=references,
            recommended_attorneys=attorneys,  # Changed to plural
            email_template=email_template,
            confidence_score=confidence
        )

        logger.info("\n" + "="*80)
        logger.info("RISK ANALYSIS COMPLETE")
        logger.info("="*80)
        logger.info(f"Identified {len(risks)} risks")
        logger.info(f"Found {len(references)} references")
        logger.info(f"Recommended {len(attorneys)} attorneys")  # Changed logging
        logger.info(f"Top attorney: {attorneys[0].name}")
        logger.info(f"Confidence: {confidence}%")
        
        return response
    
    def _retrieve_rag_context(self, request: RiskAnalysisRequest) -> Dict[str, Any]:
        """
        Retrieve relevant documents from both indexes using RAG
        """
        logger.info("\n" + "-"*80)
        logger.info("STEP 1: RAG DOCUMENT RETRIEVAL")
        logger.info("-"*80)
        
        # Build search query focused on practice area and company context
        search_query = f"{request.practicearea} legal compliance risks regulations"
        logger.info(f"Search Query: {search_query}")
        
        # Search both indexes
        rag_results = self.ai_search.search_both_indexes(search_query, top_per_index=3)
        
        # Log retrieved context
        logger.info(f"\nRETRIEVED RAG CONTEXT:")
        logger.info(f"  - Internal Documents: {len(rag_results['internal'])}")
        logger.info(f"  - Historical Engagements: {len(rag_results['historical'])}")
        
        if len(rag_results['internal']) == 0 and len(rag_results['historical']) == 0:
            logger.warning("WARNING: No RAG documents retrieved. Analysis will rely only on public sources.")
        
        return rag_results
    
    def _get_relevant_public_sources(self, practice_area: str) -> List[Dict[str, Any]]:
        """
        Query public data sources for relevant news/updates
        """
        logger.info("\n" + "-"*80)
        logger.info("STEP 2: PUBLIC DATA SOURCE QUERY")
        logger.info("-"*80)
        
        # Map practice area to risk areas in database
        risk_area_mapping = {
            "Corporate M&A": ["Corporate Governance", "Securities Law"],
            "Data Privacy": ["Data Protection"],
            "Intellectual Property": ["Intellectual Property"],
            "Tax": ["Tax"],
            "Employment": ["Employment"],
            "Compliance": ["Data Protection", "Corporate Governance", "Securities Law"],
            "Securities Law": ["Securities Law"],
            "Banking": ["Banking"],
            "Real Estate": ["Real Estate"]
        }
        
        risk_areas = risk_area_mapping.get(practice_area, [practice_area])
        logger.info(f"Mapped practice area '{practice_area}' to risk areas: {risk_areas}")
        
        all_sources = []
        for risk_area in risk_areas:
            sources = self.public_source_service.get_public_sources(
                risk_area=risk_area,
                enrichment_status="completed"
            )
            all_sources.extend(sources[:3])  # Top 3 per risk area
        
        logger.info(f"Found {len(all_sources)} relevant public sources")
        for idx, source in enumerate(all_sources, 1):
            logger.info(f"\n  Source {idx}:")
            logger.info(f"    Title: {source['title']}")
            logger.info(f"    Risk Area: {source.get('risk_area', 'N/A')}")
            logger.info(f"    Impact: {source.get('impact_level', 'N/A')}")
            logger.info(f"    URL: {source['reference']['url']}")
        
        return all_sources
    
    def _build_risk_analysis_prompt(
        self, 
        request: RiskAnalysisRequest,
        rag_context: Dict[str, Any],
        public_sources: List[Dict[str, Any]]
    ) -> str:
        """
        Build comprehensive prompt for LLM with all context
        """
        logger.info("\n" + "-"*80)
        logger.info("STEP 3: BUILDING LLM PROMPT")
        logger.info("-"*80)
        
        # Build context sections - only include if we have content
        internal_context = ""
        if rag_context['internal']:
            internal_docs = "\n\n".join([
                f"[Internal Document: {doc['source']}]\n{doc['content'][:2000]}"
                for doc in rag_context['internal'] if doc['content']
            ])
            if internal_docs:
                internal_context = f"INTERNAL LEGAL KNOWLEDGE BASE:\n{internal_docs}\n\n"
        
        historical_context = ""
        if rag_context['historical']:
            historical_docs = "\n\n".join([
                f"[Historical Engagement: {doc['source']}]\n{doc['content'][:2000]}"
                for doc in rag_context['historical'] if doc['content']
            ])
            if historical_docs:
                historical_context = f"HISTORICAL ENGAGEMENT DATA:\n{historical_docs}\n\n"
        
        public_context = ""
        if public_sources:
            public_docs = "\n\n".join([
                f"[Public Source: {src['title']}]\n"
                f"Risk Area: {src.get('risk_area', 'N/A')}\n"
                f"Summary: {src.get('summary', 'N/A')}\n"
                f"Impact: {src.get('impact_level', 'N/A')}\n"
                f"Jurisdiction: {src.get('jurisdiction', 'N/A')}"
                for src in public_sources
            ])
            public_context = f"RECENT PUBLIC LEGAL DEVELOPMENTS:\n{public_docs}\n\n"
        
        # Build the prompt
        prompt = f"""You are a legal risk analysis expert. Analyze potential legal risks for a company based on the provided context.

COMPANY INFORMATION:
- Company Name: {request.companyName}
- Practice Area of Interest: {request.practicearea}
- Contact Email: {request.companyemail}
- Contact Phone: {request.companyphonenumber}

{internal_context}{historical_context}{public_context}

TASK:
Based on the above context, identify 3-5 specific legal risks this company might face in the "{request.practicearea}" practice area.

IMPORTANT INSTRUCTIONS:
1. Be specific and actionable in describing each risk
2. Focus on risks relevant to the "{request.practicearea}" practice area
3. If you have internal knowledge base or historical data, use those insights to provide company-specific risks
4. If you only have public source data, focus on general industry risks based on recent legal developments
5. Consider the company's likely jurisdiction and operations based on available context

Return your analysis as a JSON object with this structure:
{{
    "risks": [
        "Specific risk 1 with clear description",
        "Specific risk 2 with clear description",
        "Specific risk 3 with clear description"
    ],
    "confidence_score": 85,
    "reasoning": "Brief explanation of your analysis approach and data sources used"
}}

IMPORTANT: Return ONLY valid JSON, no additional text or markdown formatting."""

        logger.info("Prompt built successfully")
        logger.info(f"  - Prompt length: {len(prompt)} characters")
        logger.info(f"  - Internal docs included: {len(rag_context['internal'])}")
        logger.info(f"  - Historical docs included: {len(rag_context['historical'])}")
        logger.info(f"  - Public sources included: {len(public_sources)}")
        
        logger.info("\n" + "-"*80)
        logger.info("FULL PROMPT SENT TO LLM:")
        logger.info("-"*80)
        logger.info(prompt)
        logger.info("-"*80)
        
        return prompt
    
    def _get_llm_risk_analysis(
        self, 
        prompt: str, 
        public_sources: List[Dict[str, Any]]
    ) -> Tuple[List[str], List[ReferenceItem], float]:
        """
        Call Azure OpenAI to analyze risks
        """
        logger.info("\n" + "-"*80)
        logger.info("STEP 4: LLM RISK ANALYSIS")
        logger.info("-"*80)
        logger.info(f"Model: {settings.AZURE_OPENAI_DEPLOYMENT_NAME}")
        logger.info(f"Temperature: {settings.AZURE_OPENAI_TEMPERATURE}")
        logger.info(f"Max Tokens: {settings.AZURE_OPENAI_MAX_TOKENS}")
        
        try:
            response = self.llm_client.chat.completions.create(
                model=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a legal risk analysis expert. Provide thorough, accurate risk assessments in JSON format."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=settings.AZURE_OPENAI_TEMPERATURE,
                max_tokens=settings.AZURE_OPENAI_MAX_TOKENS
            )
            
            llm_response = response.choices[0].message.content.strip()
            
            logger.info("\n" + "-"*80)
            logger.info("LLM RAW RESPONSE:")
            logger.info("-"*80)
            logger.info(llm_response)
            logger.info("-"*80)
            
            # Parse JSON response
            # Remove markdown code blocks if present
            if llm_response.startswith("```json"):
                llm_response = llm_response.replace("```json", "").replace("```", "").strip()
            elif llm_response.startswith("```"):
                llm_response = llm_response.replace("```", "").strip()
            
            result = json.loads(llm_response)
            
            risks = result.get("risks", [])
            confidence = result.get("confidence_score",85)
            reasoning = result.get("reasoning", "")
            
            logger.info("\nLLM ANALYSIS PARSED:")
            logger.info(f"  - Risks identified: {len(risks)}")
            logger.info(f"  - Confidence score: {confidence:.2%}")
            logger.info(f"  - Reasoning: {reasoning}")
            
            for idx, risk in enumerate(risks, 1):
                logger.info(f"\n  Risk {idx}: {risk}")
            
            # Build references from public sources
            references = [
                ReferenceItem(
                    label=f"{src.get('risk_area', 'Legal Update')} - {src['title'][:50]}...",
                    url=src['reference']['url']
                )
                for src in public_sources[:5]  # Top 5 references
            ]
            
            logger.info(f"\nGenerated {len(references)} reference links")
            
            return risks, references, confidence
            
        except Exception as e:
            logger.error(f"LLM Error: {str(e)}")
            # Fallback risks
            return [
                "General compliance risk in the specified practice area requires assessment",
                "Regulatory changes may impact operations and require monitoring",
                "Documentation and reporting requirements need review"
            ], [], 50
    
    def _find_matching_attorneys(
        self, 
        practice_area: str,
        rag_context: Dict[str, Any],
        top_n: int = 3
    ) -> List[RecommendedAttorney]:
        """
        Find the top N matching attorneys based on practice area and experience
        
        Args:
            practice_area: Target practice area
            rag_context: RAG context with historical data
            top_n: Number of top attorneys to return (default: 3)
        """
        logger.info("\n" + "-"*80)
        logger.info("STEP 5: ATTORNEY MATCHING")
        logger.info("-"*80)
        logger.info(f"Target Practice Area: {practice_area}")
        logger.info(f"Returning top {top_n} attorneys")
        
        # Get attorneys with matching practice area
        attorneys = self.attorney_service.get_attorneys(practice_area=practice_area)
        
        logger.info(f"\nFound {len(attorneys)} attorneys in '{practice_area}'")
        
        if not attorneys:
            logger.warning("No attorneys found for practice area, searching all attorneys...")
            attorneys = self.attorney_service.get_attorneys()
        
        if not attorneys:
            logger.warning("No attorneys found in database")
            return [RecommendedAttorney(
                name="General Counsel",
                role="Partner",
                reason="No attorneys available in the system",
                match_score=0
            )]
        
        # Extract attorney IDs from historical engagements
        historical_attorney_ids = set()
        for doc in rag_context.get('historical', []):
            content = doc.get('content', '')
            import re
            ids = re.findall(r'ATT-[A-Z0-9]{8}', content)
            historical_attorney_ids.update(ids)
        
        logger.info(f"\nHistorical Attorney IDs found: {historical_attorney_ids}")
        
        # Score all attorneys
        attorney_scores = []
        
        for attorney in attorneys:
            score = 0
            
            # Base score for practice area match
            for pa in attorney.get('practice_areas', []):
                if pa['area'] == practice_area:
                    score += 40
                    # Proficiency bonus
                    proficiency_bonus = {
                        'Expert': 20,
                        'Advanced': 15,
                        'Intermediate': 10,
                        'Beginner': 5
                    }
                    score += proficiency_bonus.get(pa['proficiency'], 0)
            
            # Seniority bonus
            seniority_bonus = {
                'Senior Partner': 20,
                'Partner': 15,
                'Senior Associate': 10,
                'Associate': 5
            }
            score += seniority_bonus.get(attorney['seniority'], 0)
            
            # Experience bonus
            score += min(attorney['years_of_experience'], 20)
            
            # Historical engagement bonus
            if attorney['attorney_id'] in historical_attorney_ids:
                score += 30
                logger.info(f"  Historical match bonus for {attorney['name']}!")
            
            attorney_scores.append({
                'attorney': attorney,
                'score': score
            })
            
            logger.info(f"\n  Attorney: {attorney['name']}")
            logger.info(f"    ID: {attorney['attorney_id']}")
            logger.info(f"    Seniority: {attorney['seniority']}")
            logger.info(f"    Experience: {attorney['years_of_experience']} years")
            logger.info(f"    Practice Areas: {[pa['area'] for pa in attorney.get('practice_areas', [])]}")
            logger.info(f"    Score: {score}")
        
        # Sort by score (descending)
        attorney_scores.sort(key=lambda x: x['score'], reverse=True)
        
        # Get top N attorneys
        top_attorneys = attorney_scores[:top_n]
        
        # Build RecommendedAttorney objects
        recommended_list = []

        for idx, item in enumerate(top_attorneys, 1):
            attorney = item['attorney']
            score = item['score']
            
            practice_areas_str = ", ".join([pa['area'] for pa in attorney.get('practice_areas', [])])
            if not practice_areas_str:
                practice_areas_str = "General Practice"
            
            reason = f"Specializes in {practice_areas_str} with {attorney['years_of_experience']} years of experience. "
            
            if attorney['attorney_id'] in historical_attorney_ids:
                reason += "Has handled similar matters based on historical engagements."
            
            # Remove "Match score: {score}/100" from reason
            
            recommended_list.append(RecommendedAttorney(
                name=attorney['name'],
                role=f"{attorney['seniority']}, {practice_areas_str}",
                reason=reason,
                match_score=score,  # NEW FIELD
                attorney_id=attorney['attorney_id'],
                email=attorney['email']
            ))
            
            if idx == 1:
                logger.info(f"\nTOP MATCH:")
            else:
                logger.info(f"\nRANK #{idx}:")
            logger.info(f"  Name: {attorney['name']}")
            logger.info(f"  Role: {attorney['seniority']}")
            logger.info(f"  Match Score: {score}")  # Updated logging
            logger.info(f"  Reason: {reason}")
        
        return recommended_list
    
    def _generate_email_template(
        self,
        request: RiskAnalysisRequest,
        attorney: RecommendedAttorney,
        risks: List[str]
    ) -> str:
        """
        Generate a professional email template
        """
        logger.info("\n" + "-"*80)
        logger.info("STEP 6: EMAIL TEMPLATE GENERATION")
        logger.info("-"*80)
        
        risks_formatted = "\n".join([f"• {risk}" for risk in risks])
        
        # Build contact info section with optional fields
        contact_info_lines = [f"- Company: {request.companyName}"]
        if request.companyemail:
            contact_info_lines.append(f"- Email: {request.companyemail}")
        if request.companyphonenumber:
            contact_info_lines.append(f"- Phone: {request.companyphonenumber}")
        
        contact_info = "\n".join(contact_info_lines)
        
        template = f"""Dear {attorney.name},

    I hope this email finds you well. I am reaching out regarding {request.companyName}, a client seeking legal counsel in the {request.practicearea} practice area.

    Based on our preliminary analysis, we have identified the following potential legal risk areas that require attention:

    {risks_formatted}

    Given your expertise in {request.practicearea} and your track record handling similar matters, we believe you would be an excellent fit for this engagement.

    Client Contact Information:
    {contact_info}

    Would you be available for an initial consultation to discuss these matters in more detail? Please let me know your availability, and I will coordinate with the client.

    Best regards,
    Legal Services Team
    """
        
        logger.info("Email template generated")
        logger.info(f"  - Length: {len(template)} characters")
        
        return template