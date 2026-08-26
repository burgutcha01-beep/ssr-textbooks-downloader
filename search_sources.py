#!/usr/bin/env python3
"""
Automated Source Finder for SSR Textbooks
Searches Archive.org and validates URLs
"""

import json
import requests
from typing import Dict, List, Optional
import logging
from datetime import datetime
import time
from urllib.parse import urljoin

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('search.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

# Search patterns for each country/subject/language
SEARCH_PATTERNS = {
    "Russia": {
        "history": {
            "query": "учебник история россии",
            "lang": "ru"
        },
        "world_history": {
            "query": "вseобщая история учебник",
            "lang": "ru"
        },
        "native_language": {
            "query": "русский язык учебник",
            "lang": "ru"
        },
        "reading": {
            "query": "литература учебник",
            "lang": "ru"
        }
    },
    "Ukraine": {
        "history": {
            "query": "історія України підручник",
            "lang": "uk"
        },
        "world_history": {
            "query": "всесвітня історія підручник",
            "lang": "uk"
        },
        "native_language": {
            "query": "українська мова підручник",
            "lang": "uk"
        },
        "reading": {
            "query": "українська література підручник",
            "lang": "uk"
        }
    },
    "Belarus": {
        "history": {
            "query": "гісторыя беларусі учебник",
            "lang": "be"
        },
        "world_history": {
            "query": "сусветная гісторыя учебник",
            "lang": "be"
        },
        "native_language": {
            "query": "беларуская мова учебник",
            "lang": "be"
        },
        "reading": {
            "query": "беларуская літаратура учебник",
            "lang": "be"
        }
    },
    "Kazakhstan": {
        "history": {
            "query": "қазақстан тарихы оқулық",
            "lang": "kk"
        },
        "world_history": {
            "query": "әлем тарихы оқулық",
            "lang": "kk"
        },
        "native_language": {
            "query": "қазақ тілі оқулық",
            "lang": "kk"
        },
        "reading": {
            "query": "әдебиет оқулық",
            "lang": "kk"
        }
    },
}

class SourceFinder:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(headers)
        self.found_sources = {}
        self.failed_searches = []

    def search_archive_org(self, query: str, mediatype: str = "texts") -> List[Dict]:
        """
        Search Archive.org for textbooks
        """
        try:
            logger.info(f"Searching Archive.org: {query}")
            
            # Archive.org API endpoint
            url = "https://archive.org/advancedsearch.php"
            params = {
                'q': query,
                'fl': 'identifier,title,date,downloads',
                'output': 'json',
                'rows': 50,
                'sort': 'downloads desc'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = data.get('response', {}).get('docs', [])
            
            logger.info(f"Found {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Search failed: {str(e)[:100]}")
            return []

    def validate_pdf_url(self, archive_id: str) -> Optional[str]:
        """
        Check if PDF exists in Archive.org item
        """
        try:
            # Try to get metadata
            metadata_url = f"https://archive.org/metadata/{archive_id}"
            response = self.session.get(metadata_url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            files = data.get('files', [])
            
            # Look for PDF files
            for file in files:
                if file.get('name', '').endswith('.pdf'):
                    pdf_url = f"https://archive.org/download/{archive_id}/{file.get('name')}"
                    logger.info(f"✓ Found PDF: {pdf_url[:60]}...")
                    return pdf_url
            
            # If no direct PDF, try generic download
            pdf_url = f"https://archive.org/download/{archive_id}/{archive_id}.pdf"
            logger.warning(f"No direct PDF found, trying generic: {pdf_url[:60]}...")
            return pdf_url
            
        except Exception as e:
            logger.warning(f"Validation failed for {archive_id}: {str(e)[:50]}")
            return None

    def search_and_validate(self, query: str) -> Optional[str]:
        """
        Search and validate in one go
        """
        results = self.search_archive_org(query)
        
        for result in results:
            archive_id = result.get('identifier')
            if not archive_id:
                continue
            
            pdf_url = self.validate_pdf_url(archive_id)
            if pdf_url:
                return pdf_url
            
            # Rate limiting
            time.sleep(0.5)
        
        return None

    def find_all_sources(self) -> Dict:
        """
        Search for all countries/subjects
        """
        sources = {}
        
        for country, subjects in SEARCH_PATTERNS.items():
            logger.info(f"\n=== Searching {country} ===")
            sources[country] = {}
            
            for subject, config in subjects.items():
                logger.info(f"\nSearching {country} - {subject}")
                sources[country][subject] = {}
                
                query = config['query']
                
                # Try to find for grades 9, 10, 11
                for grade in [9, 10, 11]:
                    grade_query = f"{query} {grade} класс"
                    
                    url = self.search_and_validate(grade_query)
                    
                    if url:
                        sources[country][subject][str(grade)] = [url]
                        logger.info(f"✓ Grade {grade}: {url[:60]}...")
                    else:
                        sources[country][subject][str(grade)] = [None]
                        logger.warning(f"✗ Grade {grade}: Not found")
                        self.failed_searches.append(f"{country}/{subject}/grade{grade}")
                    
                    # Rate limiting between requests
                    time.sleep(1)
        
        return sources

    def fill_empty_sources(self, sources: Dict) -> Dict:
        """
        Fill empty entries with generic search fallback
        """
        for country, subjects in sources.items():
            for subject, grades in subjects.items():
                for grade, urls in grades.items():
                    if not urls or urls[0] is None:
                        # Try generic search without grade
                        logger.info(f"Fallback search for {country}/{subject}")
                        pattern = SEARCH_PATTERNS.get(country, {}).get(subject, {})
                        if pattern:
                            url = self.search_and_validate(pattern.get('query', ''))
                            if url:
                                sources[country][subject][grade] = [url]
                            time.sleep(0.5)
        
        return sources

    def save_sources(self, sources: Dict, filename: str = 'sources.json'):
        """
        Save found sources to JSON
        """
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(sources, f, ensure_ascii=False, indent=2)
        
        logger.info(f"\nSources saved to {filename}")

    def print_summary(self, sources: Dict):
        """
        Print search summary
        """
        total = 0
        found = 0
        
        for country, subjects in sources.items():
            for subject, grades in subjects.items():
                for grade, urls in grades.items():
                    total += 1
                    if urls and urls[0]:
                        found += 1
        
        logger.info(f"\n{'='*50}")
        logger.info(f"SEARCH SUMMARY")
        logger.info(f"{'='*50}")
        logger.info(f"Total entries: {total}")
        logger.info(f"Found: {found} ({100*found/total:.1f}%)")
        logger.info(f"Not found: {total-found}")
        logger.info(f"Failed searches: {len(self.failed_searches)}")
        
        if self.failed_searches:
            logger.info(f"\nFailed to find:")
            for item in self.failed_searches[:10]:
                logger.info(f"  - {item}")
            if len(self.failed_searches) > 10:
                logger.info(f"  ... and {len(self.failed_searches)-10} more")
        
        logger.info(f"{'='*50}\n")

    def run(self):
        """
        Main execution
        """
        logger.info("Starting Source Finder")
        logger.info(f"Time: {datetime.now()}")
        
        # Search for all sources
        sources = self.find_all_sources()
        
        # Try to fill empty entries
        logger.info("\nFilling empty entries...")
        sources = self.fill_empty_sources(sources)
        
        # Save results
        self.save_sources(sources)
        
        # Print summary
        self.print_summary(sources)
        
        logger.info("✓ Source finder complete!")


if __name__ == '__main__':
    finder = SourceFinder()
    finder.run()
