#!/usr/bin/env python3
"""
SSR Textbooks Downloader
Automatically downloads PDFs for 15 CIS countries
Russia, Ukraine, Belarus, Kazakhstan, Uzbekistan, Kyrgyzstan, Tajikistan, Turkmenistan,
Azerbaijan, Armenia, Georgia, Moldova, Lithuania, Latvia, Estonia
"""

import os
import json
import requests
import zipfile
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import logging
from urllib.parse import urljoin, urlparse

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

    def download_file(self, url: str, filepath: Path, country: str, subject: str, grade: int) -> bool:
        """
        Download a file with retries
        """
        for attempt in range(MAX_RETRIES):
            try:
                logger.info(f"Downloading [{attempt+1}/{MAX_RETRIES}]: {url[:60]}...")
                response = self.session.get(url, timeout=TIMEOUT, stream=True)
                response.raise_for_status()
                
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
                        
                        # Create filename
                        filename = f"grade_{grade}_{subject}.pdf"
                        filepath = country_dir / filename
                        
                        # Skip if already downloaded
                        if filepath.exists():
                            logger.info(f"Already exists: {filename}")
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
            f.write("# SSR Textbooks Download Log\n\n")
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
        logger.info("Starting SSR Textbooks Downloader")
        
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
