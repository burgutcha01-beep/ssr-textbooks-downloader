#!/usr/bin/env python3
"""
Validate sources.json URLs
Checks if URLs are accessible and return PDF
"""

import json
import requests
from pathlib import Path
import logging
from typing import Dict, List

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

def validate_url(url: str, timeout: int = 10) -> bool:
    """
    Check if URL is accessible
    """
    if not url or url == "None":
        return False
    
    try:
        response = requests.head(url, timeout=timeout, headers=headers, allow_redirects=True)
        if response.status_code == 200:
            logger.info(f"✓ Valid: {url[:60]}...")
            return True
        else:
            logger.warning(f"✗ Status {response.status_code}: {url[:60]}...")
            return False
    except Exception as e:
        logger.warning(f"✗ Invalid: {url[:60]}... ({str(e)[:30]}...)")
        return False

def validate_sources(filename: str = 'sources.json') -> Dict:
    """
    Validate all URLs in sources.json
    """
    if not Path(filename).exists():
        logger.error(f"File not found: {filename}")
        return {}
    
    with open(filename, 'r', encoding='utf-8') as f:
        sources = json.load(f)
    
    stats = {
        'total': 0,
        'valid': 0,
        'invalid': 0
    }
    
    logger.info("Validating sources.json...\n")
    
    for country, subjects in sources.items():
        logger.info(f"\n{country}:")
        
        for subject, grades in subjects.items():
            for grade, urls in grades.items():
                stats['total'] += 1
                
                if not urls or not urls[0]:
                    logger.warning(f"  {subject} grade {grade}: EMPTY")
                    stats['invalid'] += 1
                    continue
                
                if validate_url(urls[0]):
                    stats['valid'] += 1
                else:
                    stats['invalid'] += 1
    
    logger.info(f"\n\n{'='*50}")
    logger.info(f"VALIDATION SUMMARY")
    logger.info(f"{'='*50}")
    logger.info(f"Total: {stats['total']}")
    logger.info(f"Valid: {stats['valid']} ({100*stats['valid']/stats['total']:.1f}%)")
    logger.info(f"Invalid/Empty: {stats['invalid']}")
    logger.info(f"{'='*50}\n")
    
    return stats

if __name__ == '__main__':
    validate_sources()
