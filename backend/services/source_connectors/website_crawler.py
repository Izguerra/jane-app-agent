import httpx
import hashlib
from typing import Dict, Any, List, Optional
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import nanoid

from .base_connector import BaseConnector
from backend.knowledge_base import KnowledgeBaseService

class WebsiteCrawler(BaseConnector):
    """Connector for crawling and indexing website content"""
    
    def __init__(self, source_id: str, workspace_id: str, config: Dict[str, Any]):
        super().__init__(source_id, workspace_id, config)
        self.kb_service = KnowledgeBaseService()
        self.max_pages = config.get('max_pages', 50)
        self.max_depth = config.get('max_depth', 3)
    
    def validate_config(self) -> tuple[bool, Optional[str]]:
        """Validate website crawler configuration"""
        if 'url' not in self.config:
            return False, "URL is required"
        
        url = self.config['url']
        if not url.startswith(('http://', 'https://')):
            return False, "URL must start with http:// or https://"
        
        return True, None
    
    async def test_connection(self) -> tuple[bool, str]:
        """Test connection to the website"""
        url = self.config['url']
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                
                if response.status_code == 200:
                    return True, f"Successfully connected to {url}"
                else:
                    return False, f"Website returned status code {response.status_code}"
        
        except httpx.TimeoutException:
            return False, "Connection timed out"
        except httpx.RequestError as e:
            return False, f"Connection error: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
    
    async def sync(self) -> Dict[str, Any]:
        """Crawl website and index pages"""
        url = self.config['url']
        visited_urls = set()
        to_visit = [(url, 0)]  # (url, depth)
        
        documents_processed = 0
        documents_added = 0
        documents_updated = 0
        documents_failed = 0
        errors = []
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            while to_visit and documents_processed < self.max_pages:
                current_url, depth = to_visit.pop(0)
                
                if current_url in visited_urls or depth > self.max_depth:
                    continue
                
                visited_urls.add(current_url)
                
                try:
                    # Fetch page
                    response = await client.get(current_url)
                    if response.status_code != 200:
                        documents_failed += 1
                        errors.append(f"Failed to fetch {current_url}: Status {response.status_code}")
                        continue
                    
                    # Parse HTML
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Extract text content
                    # Remove script and style elements
                    for script in soup(["script", "style", "nav", "footer"]):
                        script.decompose()
                    
                    text = soup.get_text(separator='\n', strip=True)
                    
                    # Get title
                    title = soup.title.string if soup.title else current_url
                    
                    # Skip if no meaningful content
                    if len(text) < 100:
                        continue
                    
                    # Generate document ID from URL
                    url_hash = hashlib.md5(current_url.encode()).hexdigest()[:12]
                    doc_id = self._generate_doc_id(url_hash)
                    
                    # Store in knowledge base
                    self.kb_service.upsert_document(
                        doc_id=doc_id,
                        text=text,
                        metadata={
                            'title': title,
                            'url': current_url,
                            'source_type': 'website_crawler',
                            'crawled_at': datetime.now().isoformat()
                        },
                        workspace_id=self.workspace_id,
                        source_id=self.source_id
                    )
                    
                    documents_processed += 1
                    documents_added += 1
                    
                    # Extract links for further crawling
                    if depth < self.max_depth:
                        base_domain = urlparse(url).netloc
                        for link in soup.find_all('a', href=True):
                            absolute_url = urljoin(current_url, link['href'])
                            link_domain = urlparse(absolute_url).netloc
                            
                            # Only crawl same domain
                            if link_domain == base_domain and absolute_url not in visited_urls:
                                to_visit.append((absolute_url, depth + 1))
                
                except Exception as e:
                    documents_failed += 1
                    errors.append(f"Error processing {current_url}: {str(e)}")
        
        return {
            'documents_processed': documents_processed,
            'documents_added': documents_added,
            'documents_updated': documents_updated,
            'documents_failed': documents_failed,
            'errors': errors
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get crawler status"""
        return {
            'status': 'active',
            'last_synced_at': datetime.now(),
            'document_count': 0,  # Would need to query database
            'error_message': None
        }
