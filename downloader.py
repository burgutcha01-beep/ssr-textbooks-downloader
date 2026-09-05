#!/usr/bin/env python3
"""
SSR Textbooks Downloader
Automatically downloads PDFs for 15 CIS countries and Open Educational Resources
Russia, Ukraine, Belarus, Kazakhstan, Uzbekistan, Kyrgyzstan, Tajikistan, Turkmenistan,
Azerbaijan, Armenia, Georgia, Moldova, Lithuania, Latvia, Estonia + CKHG, OpenStax, etc.
"""

import os
import json
import requests
import zipfile
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import logging
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import re

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('download.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
OUTPUT_DIR = Path('textbooks')
ZIP_FILE = 'SSR_books.zip'
TIMEOUT = 30
MAX_RETRIES = 3
CHUNK_SIZE = 8192

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

class TextbookDownloader:
    def __init__(self):
        self.output_dir = OUTPUT_DIR
        self.output_dir.mkdir(exist_ok=True)
        self.download_log = []
        self.session = requests.Session()
        self.session.headers.update(headers)

    def extract_pdf_from_ckhg(self, url: str) -> Optional[str]:
        """
        Extract PDF download link from CKHG Core Knowledge page
        """
        try:
            logger.info(f"Parsing CKHG page: {url[:60]}...")
            response = self.session.get(url, timeout=TIMEOUT)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for download link patterns
            pdf_patterns = [
                # Direct PDF links
                r'href=["\']([^"\']*\.pdf)["\']',
                # Data attribute with PDF
                r'data-[a-z]+-url=["\']([^"\']*\.pdf)["\']',
                # Download button links
                r'class=["\'].*download.*["\'].*href=["\']([^"\']*)["\']',
            ]
            
            html_text = response.text
            
            for pattern in pdf_patterns:
                matches = re.findall(pattern, html_text, re.IGNORECASE)
                if matches:
                    pdf_url = matches[0]
                    # Make absolute URL
                    if not pdf_url.startswith('http'):
                        pdf_url = urljoin(url, pdf_url)
                    logger.info(f"Found PDF link: {pdf_url[:60]}...")
                    return pdf_url
            
            # Look for links in button elements
            buttons = soup.find_all(['a', 'button'], string=re.compile(r'download|pdf|скачать', re.IGNORECASE))
            for button in buttons:
                href = button.get('href')
                if href:
                    pdf_url = urljoin(url, href)
                    if '.pdf' in pdf_url.lower():
                        logger.info(f"Found PDF in button: {pdf_url[:60]}...")
                        return pdf_url
            
            logger.warning(f"No PDF link found on: {url}")
            return None
            
        except Exception as e:
            logger.error(f"Error parsing CKHG page: {str(e)[:100]}")
            return None

    def download_file(self, url: str, filepath: Path, country: str, subject: str, grade: int) -> bool:
        """
        Download a file with retries
        Handles both direct PDF links and CKHG/OpenStax page links
        """
        # Check if URL is a CKHG or OpenStax page (not direct PDF)
        if url.endswith('/') or 'coreknowledge.org' in url or 'openstax.org' in url:
            if 'coreknowledge.org' in url:
                pdf_url = self.extract_pdf_from_ckhg(url)
                if not pdf_url:
                    logger.warning(f"Could not extract PDF from CKHG: {url}")
                    self.download_log.append({
                        'country': country,
                        'subject': subject,
                        'grade': grade,
                        'filename': None,
                        'size_mb': 0,
                        'source': url,
                        'status': 'EXTRACTION_FAILED'
                    })
                    return False
                url = pdf_url
        
        for attempt in range(MAX_RETRIES):
            try:
                logger.info(f"Downloading [{attempt+1}/{MAX_RETRIES}]: {url[:60]}...")
                response = self.session.get(url, timeout=TIMEOUT, stream=True, allow_redirects=True)
                response.raise_for_status()
                
                # Check if response is actually PDF
                content_type = response.headers.get('content-type', '').lower()
                if 'pdf' not in content_type and 'application' not in content_type:
                    logger.warning(f"Response is not PDF (content-type: {content_type})")
                    if attempt == MAX_RETRIES - 1:
                        return False
                    continue
                
                total_size = int(response.headers.get('content-length', 0))
                
                with open(filepath, 'wb') as f:
                    downloaded = 0
                    for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_size:
                                percent = (downloaded / total_size) * 100
                                logger.debug(f"Progress: {percent:.1f}%")
                
                file_size = filepath.stat().st_size
                
                # Validate PDF (check magic bytes)
                with open(filepath, 'rb') as f:
                    magic = f.read(4)
                    if magic != b'%PDF':
                        logger.warning(f"File is not a valid PDF (magic bytes: {magic})")
                        filepath.unlink()
                        if attempt == MAX_RETRIES - 1:
                            return False
                        continue
                
                logger.info(f"✓ Downloaded: {filepath.name} ({file_size/1024/1024:.2f} MB)")
                
                # Log to download log
                self.download_log.append({
                    'country': country,
                    'subject': subject,
                    'grade': grade,
                    'filename': filepath.name,
                    'size_mb': round(file_size/1024/1024, 2),
                    'source': url,
                    'status': 'OK'
                })
                
                return True
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Attempt {attempt+1} failed: {str(e)[:100]}")
                if filepath.exists():
                    filepath.unlink()
                if attempt == MAX_RETRIES - 1:
                    logger.error(f"✗ Failed to download: {url}")
                    self.download_log.append({
                        'country': country,
                        'subject': subject,
                        'grade': grade,
                        'filename': None,
                        'size_mb': 0,
                        'source': url,
                        'status': f'FAILED ({str(e)[:50]})'
                    })
                    return False
        
        return False

    def setup_country_dir(self, country: str) -> Path:
        """
        Create country directory structure
        """
        country_dir = self.output_dir / country
        country_dir.mkdir(exist_ok=True)
        return country_dir

    def download_sources(self, sources: Dict) -> None:
        """
        Download all sources from database
        """
        total = len(sources)
        current = 0
        
        for country, subjects in sources.items():
            logger.info(f"\n=== Processing {country} ===")
            country_dir = self.setup_country_dir(country)
            
            for subject, grades in subjects.items():
                # Skip comments
                if subject.startswith('COMMENT'):
                    continue
                    
                for grade, urls in grades.items():
                    current += 1
                    logger.info(f"[{current}/{total}] {country} - {subject} - Grade {grade}")
                    
                    if not urls or urls[0] is None:
                        logger.warning(f"No URL for {country}/{subject}/grade {grade}")
                        self.download_log.append({
                            'country': country,
                            'subject': subject,
                            'grade': grade,
                            'filename': None,
                            'size_mb': 0,
                            'source': 'N/A',
                            'status': 'NOT_FOUND'
                        })
                        continue
                    
                    for url in urls:
                        if not url:
                            continue
                        
                        # Create filename (clean subject name)
                        clean_subject = re.sub(r'[^\w\s_-]', '', subject).replace(' ', '_')
                        filename = f"grade_{grade}_{clean_subject}.pdf"
                        filepath = country_dir / filename
                        
                        # Skip if already downloaded
                        if filepath.exists():
                            logger.info(f"Already exists: {filename}")
                            self.download_log.append({
                                'country': country,
                                'subject': subject,
                                'grade': grade,
                                'filename': filename,
                                'size_mb': filepath.stat().st_size / 1024 / 1024,
                                'source': url,
                                'status': 'ALREADY_DOWNLOADED'
                            })
                            continue
                        
                        # Try to download
                        if self.download_file(url, filepath, country, subject, grade):
                            break  # Success, move to next
        
        logger.info(f"\n=== Download Complete ===")
        logger.info(f"Total entries processed: {current}")
        logger.info(f"Successfully downloaded: {len([x for x in self.download_log if x['status'] == 'OK'])}")

    def create_download_log(self) -> None:
        """
        Create DOWNLOAD_LOG.md
        """
        log_file = self.output_dir / 'DOWNLOAD_LOG.md'
        
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write("# SSR Textbooks & OER Download Log\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("| Country | Subject | Grade | Filename | Size (MB) | Source | Status |\n")
            f.write("|---------|---------|-------|----------|-----------|--------|--------|\n")
            
            for entry in self.download_log:
                country = entry['country']
                subject = entry['subject']
                grade = entry['grade']
                filename = entry['filename'] or 'N/A'
                size = entry['size_mb']
                source = entry['source'][:50] + '...' if len(entry['source']) > 50 else entry['source']
                status = entry['status']
                
                f.write(f"| {country} | {subject} | {grade} | {filename} | {size} | {source} | {status} |\n")
        
        logger.info(f"Log saved: {log_file}")

    def create_zip(self) -> None:
        """
        Create ZIP archive
        """
        logger.info(f"Creating ZIP: {ZIP_FILE}")
        
        with zipfile.ZipFile(ZIP_FILE, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(self.output_dir):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(self.output_dir.parent)
                    zf.write(file_path, arcname)
        
        zip_size = Path(ZIP_FILE).stat().st_size / 1024 / 1024
        logger.info(f"✓ ZIP created: {ZIP_FILE} ({zip_size:.2f} MB)")
        print(f"\n📦 Archive ready: {ZIP_FILE}")

    def run(self, sources_file: str = 'sources.json') -> None:
        """
        Main execution
        """
        logger.info("Starting SSR Textbooks Downloader (with CKHG OER support)")
        
        # Load sources
        if not Path(sources_file).exists():
            logger.error(f"Sources file not found: {sources_file}")
            return
        
        with open(sources_file, 'r', encoding='utf-8') as f:
            sources = json.load(f)
        
        # Download
        self.download_sources(sources)
        
        # Create log
        self.create_download_log()
        
        # Create ZIP
        self.create_zip()
        
        logger.info("\n✓ All done!")


if __name__ == '__main__':
    downloader = TextbookDownloader()
    downloader.run()
