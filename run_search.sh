#!/bin/bash

# SSR Textbooks Source Finder
# Automatically searches and validates sources

echo "🔍 SSR Textbooks Source Finder"
echo "=============================="
echo ""
echo "This will search Archive.org and other sources"
echo "for textbooks in 15 CIS countries."
echo ""
echo "⏱️  Estimated time: 10-15 minutes"
echo ""

python3 search_sources.py

echo ""
echo "✅ Search complete!"
echo "Check sources.json for results"
echo "Then run: python3 downloader.py"
