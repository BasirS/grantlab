import requests
from bs4 import BeautifulSoup
import time
from typing import List, Dict, Any
from urllib.parse import urljoin, urlparse
import re
from config.settings import settings

class GrantDiscoveryEngine:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.delay = settings.scraping_delay
    
    def search_grants_gov(self, keywords: List[str], max_results: int = None) -> List[Dict[str, Any]]:
        max_results = max_results or settings.max_search_results
        grants = []
        
        search_terms = "+".join(keywords)
        base_url = "https://www.grants.gov/web/grants/search-grants.html"
        
        try:
            params = {
                'keywords': search_terms,
                'oppStatuses': 'forecasted|posted',
                'sortBy': 'relevancy'
            }
            
            response = self.session.get(base_url, params=params)
            if response.status_code == 200:
                grants.extend(self._parse_grants_gov_results(response.text, max_results))
            
            time.sleep(self.delay)
            
        except Exception as e:
            print(f"Error searching Grants.gov: {e}")
        
        return grants
    
    def search_foundation_grants(self, keywords: List[str]) -> List[Dict[str, Any]]:
        grants = []
        
        foundation_sources = [
            "https://foundationcenter.org/find-funding",
            "https://www.guidestar.org/",
            "https://www.candid.org/find-funding"
        ]
        
        for source in foundation_sources:
            try:
                response = self.session.get(source)
                if response.status_code == 200:
                    grants.extend(self._parse_foundation_results(response.text, keywords))
                
                time.sleep(self.delay)
                
            except Exception as e:
                print(f"Error searching {source}: {e}")
        
        return grants
    
    def get_sample_opportunities(self) -> List[Dict[str, Any]]:
        sample_grants = [
            {
                "title": "AI for Education Innovation Grant",
                "organization": "National Science Foundation",
                "deadline": "2025-10-15",
                "amount": "$500,000",
                "focus_areas": ["Educational Technology", "AI in Education", "Workforce Development"],
                "description": "Funding for innovative AI applications in educational settings, particularly those serving underrepresented communities. Priority given to projects that demonstrate scalable impact and sustainable implementation models.",
                "eligibility": "Nonprofit organizations, educational institutions, and research organizations",
                "requirements": [
                    "Demonstrate clear educational impact metrics",
                    "Include community engagement component", 
                    "Show sustainability plan beyond grant period",
                    "Partner with local educational institutions"
                ]
            },
            {
                "title": "Workforce Development Technology Grant",
                "organization": "Department of Labor",
                "deadline": "2025-11-30",
                "amount": "$750,000", 
                "focus_areas": ["Workforce Development", "Digital Skills", "Underrepresented Communities"],
                "description": "Support for technology-enabled workforce development programs targeting underrepresented populations. Emphasis on programs that provide pathways to high-growth industries and sustainable careers.",
                "eligibility": "Nonprofit organizations, workforce development boards, community colleges",
                "requirements": [
                    "Serve primarily underrepresented populations",
                    "Include industry partnership component",
                    "Demonstrate measurable employment outcomes",
                    "Provide comprehensive support services"
                ]
            }
        ]
        
        return sample_grants
    
    def _parse_grants_gov_results(self, html: str, max_results: int) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html, 'html.parser')
        grants = []
        
        grant_elements = soup.find_all('div', class_='opportunity-item')[:max_results]
        
        for element in grant_elements:
            try:
                title_elem = element.find('h3') or element.find('a')
                title = title_elem.get_text().strip() if title_elem else "Unknown Title"
                
                org_elem = element.find('span', class_='agency')
                organization = org_elem.get_text().strip() if org_elem else "Unknown Organization"
                
                deadline_elem = element.find('span', class_='deadline')
                deadline = deadline_elem.get_text().strip() if deadline_elem else "Unknown Deadline"
                
                amount_elem = element.find('span', class_='amount')
                amount = amount_elem.get_text().strip() if amount_elem else "Not specified"
                
                desc_elem = element.find('p', class_='description')
                description = desc_elem.get_text().strip() if desc_elem else ""
                
                grants.append({
                    "title": title,
                    "organization": organization,
                    "deadline": deadline,
                    "amount": amount,
                    "description": description,
                    "source": "Grants.gov"
                })
                
            except Exception as e:
                continue
        
        return grants
    
    def _parse_foundation_results(self, html: str, keywords: List[str]) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html, 'html.parser')
        grants = []
        
        return grants
    
    def filter_relevant_grants(self, grants: List[Dict[str, Any]], focus_areas: List[str] = None) -> List[Dict[str, Any]]:
        if not focus_areas:
            focus_areas = [
                "education", "technology", "workforce", "AI", "innovation",
                "BIPOC", "underrepresented", "nonprofit", "social impact",
                "youth", "adult learning", "digital skills"
            ]
        
        relevant_grants = []
        
        for grant in grants:
            relevance_score = 0
            text_to_search = f"{grant.get('title', '')} {grant.get('description', '')} {grant.get('focus_areas', [])}".lower()
            
            for area in focus_areas:
                if area.lower() in text_to_search:
                    relevance_score += 1
            
            if relevance_score >= 2:
                grant['relevance_score'] = relevance_score
                relevant_grants.append(grant)
        
        return sorted(relevant_grants, key=lambda x: x.get('relevance_score', 0), reverse=True)
    
    def search_all_sources(self, keywords: List[str] = None) -> List[Dict[str, Any]]:
        if not keywords:
            keywords = ["education", "technology", "AI", "workforce", "nonprofit"]
        
        all_grants = []
        
        all_grants.extend(self.get_sample_opportunities())
        
        try:
            all_grants.extend(self.search_grants_gov(keywords))
        except Exception as e:
            print(f"Grants.gov search failed: {e}")
        
        try:
            all_grants.extend(self.search_foundation_grants(keywords))
        except Exception as e:
            print(f"Foundation search failed: {e}")
        
        return self.filter_relevant_grants(all_grants)