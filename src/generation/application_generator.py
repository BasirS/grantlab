from typing import List, Dict, Any, Optional
from llama_index.llms.ollama import Ollama
from llama_index.core.llms import ChatMessage, MessageRole
import re
from config.settings import settings
from src.rag.vector_store import GrantVectorStore

class GrantApplicationGenerator:
    def __init__(self, vector_store: GrantVectorStore):
        self.llm = Ollama(
            model=settings.llm_model,
            base_url=settings.ollama_base_url,
            request_timeout=settings.llm_request_timeout
        )
        self.vector_store = vector_store
    
    def generate_application(self, 
                           grant_opportunity: Dict[str, Any],
                           sections_needed: List[str] = None) -> Dict[str, str]:
        
        if not sections_needed:
            sections_needed = [
                "project_overview", 
                "organizational_background",
                "project_description", 
                "intended_outcomes",
                "implementation_plan",
                "sustainability_plan"
            ]
        
        application_sections = {}
        
        for section in sections_needed:
            section_content = self._generate_section(grant_opportunity, section)
            application_sections[section] = section_content
        
        return application_sections
    
    def _generate_section(self, grant_opportunity: Dict[str, Any], section_type: str) -> str:
        relevant_examples = self._get_relevant_examples(grant_opportunity, section_type)
        org_voice = self.vector_store.get_organizational_voice_examples()
        
        system_prompt = self._build_system_prompt(section_type)
        user_prompt = self._build_user_prompt(grant_opportunity, relevant_examples, org_voice, section_type)
        
        messages = [
            ChatMessage(role=MessageRole.SYSTEM, content=system_prompt),
            ChatMessage(role=MessageRole.USER, content=user_prompt)
        ]
        
        try:
            response = self.llm.chat(messages)
            content = response.message.content

            return self._post_process_content(content, section_type)

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Error generating {section_type}: {e}")
            print(f"Full error: {error_details}")
            return f"Error generating {section_type} section. Please try again. (Check console for details)"
    
    def _get_relevant_examples(self, grant_opportunity: Dict[str, Any], section_type: str) -> List[str]:
        query_parts = [
            grant_opportunity.get("title", ""),
            " ".join(grant_opportunity.get("focus_areas", [])),
            section_type.replace("_", " ")
        ]
        
        query = " ".join(query_parts)
        results = self.vector_store.search_similar(query, top_k=3)
        
        return [result["text"] for result in results if result["text"]]
    
    def _build_system_prompt(self, section_type: str) -> str:
        base_prompt = """You are a grant writing assistant for Cambio Labs, a nonprofit innovation hub dedicated to empowering underestimated BIPOC youth and adults through digital education, green workforce training, and entrepreneurship programs.

Your writing should be:
- Professional yet warm and human-centered
- Focused on impact and community empowerment
- Specific about measurable outcomes
- Authentic to Cambio Labs' mission and voice
- Natural and conversational, avoiding overly formal or robotic language
- Free of typos, double punctuation, or formatting errors

Use natural connecting words like 'where' and 'which' to create flowing paragraphs. Write in complete paragraphs rather than bullet points or numbered lists unless specifically requested. Use only single periods, no double periods (..) or double hyphens (--)."""

        section_prompts = {
            "project_overview": "Write a compelling 3-4 sentence project overview that captures the essence of the proposed work and its alignment with both the grant opportunity and Cambio Labs' mission.",
            
            "organizational_background": "Describe Cambio Labs' background, mission, and relevant experience. Focus on our work with underestimated BIPOC communities, the Journey platform, and our track record of impact.",
            
            "project_description": "Provide a detailed description of the proposed project, explaining how it builds on Cambio Labs' existing work and addresses the specific needs outlined in the grant opportunity.",
            
            "intended_outcomes": "Describe the expected outcomes and impact of the project, including specific metrics and how success will be measured.",
            
            "implementation_plan": "Outline the project implementation approach, timeline, and key milestones.",
            
            "sustainability_plan": "Explain how the project will be sustained beyond the grant period, including revenue models and long-term planning."
        }
        
        return f"{base_prompt}\n\nFor this section ({section_type}): {section_prompts.get(section_type, 'Write appropriate content for this grant application section.')}"
    
    def _build_user_prompt(self, grant_opportunity: Dict[str, Any], 
                          relevant_examples: List[str], 
                          org_voice: List[str],
                          section_type: str) -> str:
        
        prompt = f"""Grant Opportunity Details:
Title: {grant_opportunity.get('title', 'Unknown')}
Organization: {grant_opportunity.get('organization', 'Unknown')}
Amount: {grant_opportunity.get('amount', 'Not specified')}
Focus Areas: {', '.join(grant_opportunity.get('focus_areas', []))}
Description: {grant_opportunity.get('description', '')}

Requirements: {grant_opportunity.get('requirements', [])}

Relevant Examples from Past Applications:
"""
        
        for i, example in enumerate(relevant_examples[:2]):
            prompt += f"\nExample {i+1}: {example}\n"
        
        prompt += "\nCambio Labs Organizational Voice Examples:\n"
        for i, voice_example in enumerate(org_voice[:3]):
            prompt += f"\nVoice Example {i+1}: {voice_example}\n"
        
        prompt += f"""
Based on this grant opportunity and using Cambio Labs' authentic voice and approach, write the {section_type.replace('_', ' ')} section of the grant application.

Remember:
- Stay true to Cambio Labs' mission of empowering underestimated BIPOC youth and adults
- Reference the Journey platform where relevant
- Use specific, measurable impact metrics
- Write in flowing paragraphs with natural language
- Be conversational and human-centered, not robotic
- Focus on community empowerment and equitable access

Write the section now:"""
        
        return prompt
    
    def _post_process_content(self, content: str, section_type: str) -> str:
        content = content.strip()

        # Remove markdown formatting
        content = re.sub(r'\*\*([^*]+)\*\*', r'\1', content)
        content = re.sub(r'\*([^*]+)\*', r'\1', content)

        # Remove bullet points
        content = re.sub(r'^\s*[-•]\s*', '', content, flags=re.MULTILINE)

        # Fix multiple newlines
        content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)

        # AGGRESSIVE FIX: Remove ALL double punctuation - run multiple times
        for _ in range(3):  # Run 3 times to catch nested issues
            content = re.sub(r'\.\.+', '.', content)  # Multiple periods to single
            content = re.sub(r',,+', ',', content)    # Multiple commas to single
            content = re.sub(r'--+', '-', content)    # Multiple hyphens to single
            content = re.sub(r'  +', ' ', content)    # Multiple spaces to single

        # Fix specific patterns like "2.. 0" to "2.0"
        content = re.sub(r'(\d)\.\s+(\d)', r'\1.\2', content)

        # Remove period before another punctuation
        content = re.sub(r'\.([,;:])', r'\1', content)

        # Fix spacing around punctuation
        content = re.sub(r'\s+([.,;:!?])', r'\1', content)  # Remove space before punctuation
        content = re.sub(r'([.,;:!?])([A-Z])', r'\1 \2', content)  # Add space after punctuation before capital

        # Ensure single space after sentence-ending punctuation
        content = re.sub(r'([.!?])\s+', r'\1 ', content)

        # Final cleanup: ensure content ends with a period
        if content and not content[-1] in '.!?':
            content += '.'

        return content
    
    def refine_application(self, application: Dict[str, str], 
                          feedback: str) -> Dict[str, str]:
        refined_application = {}
        
        for section, content in application.items():
            refined_content = self._refine_section(content, feedback, section)
            refined_application[section] = refined_content
        
        return refined_application
    
    def _refine_section(self, content: str, feedback: str, section_type: str) -> str:
        system_prompt = f"""You are refining a {section_type} section of a grant application for Cambio Labs based on user feedback.

CRITICAL FORMATTING RULES:
- Use ONLY single periods (.) at the end of sentences - NEVER double periods (..)
- Use ONLY single hyphens (-) - NEVER double hyphens (--)
- Write professional grant language without typos or formatting errors
- Proofread carefully for double punctuation before responding"""

        user_prompt = f"""Original content:
{content}

Feedback to address:
{feedback}

Please revise the content to address the feedback while maintaining Cambio Labs' authentic voice and mission focus. Keep the writing natural, conversational, and human-centered.

CRITICAL: Use only single periods (.) - NEVER double periods (..). Check your output carefully."""
        
        messages = [
            ChatMessage(role=MessageRole.SYSTEM, content=system_prompt),
            ChatMessage(role=MessageRole.USER, content=user_prompt)
        ]
        
        try:
            response = self.llm.chat(messages)
            return self._post_process_content(response.message.content, section_type)
        except Exception as e:
            print(f"Error refining {section_type}: {e}")
            return content