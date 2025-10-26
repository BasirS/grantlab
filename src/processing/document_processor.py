import os
import re
from typing import List, Dict, Any
from pathlib import Path

class GrantDocumentProcessor:
    def __init__(self, data_dir: str = "./examples"):
        self.data_dir = Path(data_dir)
        
    def load_grant_documents(self) -> List[Dict[str, Any]]:
        documents = []
        
        for file_path in self.data_dir.glob("*.txt"):
            if file_path.name.startswith("DATA") or file_path.name.startswith("Scaling"):
                try:
                    # Try UTF-8 first, fallback to Windows-1252
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                    except UnicodeDecodeError:
                        with open(file_path, 'r', encoding='cp1252', errors='replace') as f:
                            content = f.read()
                    
                    doc = self._parse_grant_document(content, file_path.stem)
                    if doc:
                        documents.append(doc)
                        
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")
        
        return documents
    
    def _parse_grant_document(self, content: str, filename: str) -> Dict[str, Any]:
        sections = {}
        
        if "AWS" in filename:
            sections = self._parse_aws_format(content)
            grant_type = "AWS Grant"
        elif "BRL" in filename:
            sections = self._parse_brl_format(content)
            grant_type = "BRL Catalyst"
        elif "AI for Economic" in filename:
            sections = self._parse_ai_economic_format(content)
            grant_type = "AI for Economic Empowerment"
        else:
            sections = self._parse_general_format(content)
            grant_type = "General Grant"
        
        organizational_voice = self._extract_organizational_voice(content)
        
        return {
            "filename": filename,
            "grant_type": grant_type,
            "sections": sections,
            "organizational_voice": organizational_voice,
            "full_content": content
        }
    
    def _parse_aws_format(self, content: str) -> Dict[str, str]:
        sections = {}
        
        patterns = {
            "project_overview": r"Please provide a high-level project overview.*?(?=\d+\.\d+|$)",
            "project_description": r"Describe your project in depth.*?(?=\d+\.\d+|$)",
            "intended_outcomes": r"What are the intended outcomes.*?(?=\d+\.\d+|$)",
            "driving_need": r"What is driving the need.*?(?=\d+\.\d+|$)",
            "long_term_support": r"How will you support this project long-term.*?(?=\d+\.\d+|$)",
            "technical_resources": r"Describe the resources and technical skills.*?(?=\d+\.\d+|$)"
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            if match:
                sections[key] = self._clean_text(match.group(0))
        
        return sections
    
    def _parse_brl_format(self, content: str) -> Dict[str, str]:
        sections = {}
        lines = content.split('\n')
        
        for line in lines:
            if line.strip():
                sections[f"content_{len(sections)}"] = self._clean_text(line)
        
        return sections
    
    def _parse_ai_economic_format(self, content: str) -> Dict[str, str]:
        sections = {}
        lines = content.split('\n')
        
        for line in lines:
            if line.strip():
                sections[f"content_{len(sections)}"] = self._clean_text(line)
        
        return sections
    
    def _parse_general_format(self, content: str) -> Dict[str, str]:
        sections = {}
        paragraphs = content.split('\n\n')
        
        for i, paragraph in enumerate(paragraphs):
            if paragraph.strip():
                sections[f"section_{i}"] = self._clean_text(paragraph)
        
        return sections
    
    def _extract_organizational_voice(self, content: str) -> Dict[str, List[str]]:
        voice_elements = {
            "mission_phrases": [],
            "population_focus": [],
            "program_names": [],
            "impact_metrics": [],
            "values_language": []
        }
        
        mission_patterns = [
            r"Cambio Labs.*?(?=\.|$)",
            r"Our mission.*?(?=\.|$)",
            r"dedicated to.*?(?=\.|$)"
        ]
        
        for pattern in mission_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            voice_elements["mission_phrases"].extend(matches)
        
        population_keywords = ["BIPOC", "underestimated", "youth", "adults", "communities"]
        for keyword in population_keywords:
            matches = re.findall(rf".{{0,50}}{keyword}.{{0,50}}", content, re.IGNORECASE)
            voice_elements["population_focus"].extend(matches)
        
        program_matches = re.findall(r"Journey[^.]*", content, re.IGNORECASE)
        voice_elements["program_names"].extend(program_matches)
        
        impact_patterns = [
            r"\d+[,\d]*\s+learners?",
            r"\d+x\s+increase",
            r"\$[\d,]+(?:M|K)?"
        ]
        
        for pattern in impact_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            voice_elements["impact_metrics"].extend(matches)
        
        values_keywords = ["equitable", "inclusive", "sustainable", "transformative", "regenerative"]
        for keyword in values_keywords:
            matches = re.findall(rf".{{0,30}}{keyword}.{{0,30}}", content, re.IGNORECASE)
            voice_elements["values_language"].extend(matches)
        
        return voice_elements
    
    def _clean_text(self, text: str) -> str:
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        text = re.sub(r'^\d+\.\d+\s*[�•]?\s*', '', text)
        text = re.sub(r'Please use \d+ words or less', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\(\d+-\d+ words\)', '', text, flags=re.IGNORECASE)
        
        return text
    
    def get_chunked_content(self, documents: List[Dict[str, Any]], chunk_size: int = 512) -> List[Dict[str, Any]]:
        chunks = []
        
        for doc in documents:
            for section_name, section_content in doc["sections"].items():
                if len(section_content) > chunk_size:
                    words = section_content.split()
                    for i in range(0, len(words), chunk_size // 6):
                        chunk_words = words[i:i + chunk_size // 6]
                        chunk_text = ' '.join(chunk_words)
                        
                        chunks.append({
                            "text": chunk_text,
                            "metadata": {
                                "source": doc["filename"],
                                "grant_type": doc["grant_type"],
                                "section": section_name,
                                "chunk_id": f"{doc['filename']}_{section_name}_{i}"
                            }
                        })
                else:
                    chunks.append({
                        "text": section_content,
                        "metadata": {
                            "source": doc["filename"],
                            "grant_type": doc["grant_type"],
                            "section": section_name,
                            "chunk_id": f"{doc['filename']}_{section_name}_full"
                        }
                    })
        
        return chunks