import json
import logging
import os
from time import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Set, List
from collections import defaultdict
import tldextract

logger = logging.getLogger(__name__)

class BlockedSitesTracker:
    def __init__(self, block_duration_hours: int = 24, parent_block_threshold: int = 3):
        self.block_duration = block_duration_hours * 3600
        self.parent_block_threshold = parent_block_threshold
        self.blocked_sites_file = "blocked_sites.json"
        self.blocked_sites: Dict[str, float] = {}
        self.parent_domain_counts: Dict[str, Set[str]] = defaultdict(set)
        self.blocked_parent_domains: Dict[str, float] = {}
        self.load_blocked_sites()

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            if '://' not in url:
                url = 'http://' + url
            extracted = tldextract.extract(url)
            return f"{extracted.domain}.{extracted.suffix}"
        except Exception as e:
            logger.error(f"Error extracting domain from {url}: {str(e)}")
            return url

    def load_blocked_sites(self):
        """Load blocked sites from JSON file."""
        try:
            if os.path.exists(self.blocked_sites_file):
                with open(self.blocked_sites_file, 'r') as f:
                    data = json.load(f)
                    self.blocked_sites = data.get('sites', {})
                    self.blocked_parent_domains = data.get('parent_domains', {})
                logger.info(f"Loaded {len(self.blocked_sites)} blocked sites and {len(self.blocked_parent_domains)} parent domains")
                
                # Rebuild parent domain counts
                for domain in self.blocked_sites:
                    parent = self._get_parent_domain(domain)
                    if parent:
                        self.parent_domain_counts[parent].add(domain)
        except Exception as e:
            logger.error(f"Error loading blocked sites: {str(e)}")
            self.blocked_sites = {}
            self.blocked_parent_domains = {}

    def save_blocked_sites(self):
        """Save blocked sites to JSON file."""
        try:
            data = {
                'sites': self.blocked_sites,
                'parent_domains': self.blocked_parent_domains
            }
            with open(self.blocked_sites_file, 'w') as f:
                json.dump(data, f)
            logger.info(f"Saved {len(self.blocked_sites)} blocked sites and {len(self.blocked_parent_domains)} parent domains")
        except Exception as e:
            logger.error(f"Error saving blocked sites: {str(e)}")

    def _get_parent_domain(self, url: str) -> str:
        """Extract parent domain from URL using tldextract."""
        extracted = tldextract.extract(url)
        return f"{extracted.domain}.{extracted.suffix}"

    def add_blocked_site(self, url: str):
        """Add a site to the blocked list and check parent domain patterns."""
        domain = self._extract_domain(url)
        parent_domain = self._get_parent_domain(url)
        
        # Add to blocked sites
        self.blocked_sites[domain] = time()
        logger.warning(f"Added {domain} to blocked sites at {datetime.now().isoformat()}")
        
        # Track parent domain
        if parent_domain:
            self.parent_domain_counts[parent_domain].add(domain)
            
            # Check if parent domain should be blocked
            if len(self.parent_domain_counts[parent_domain]) >= self.parent_block_threshold:
                if parent_domain not in self.blocked_parent_domains:
                    self.blocked_parent_domains[parent_domain] = time()
                    logger.warning(f"Blocking parent domain {parent_domain} due to {len(self.parent_domain_counts[parent_domain])} blocked subdomains")
        
        self.save_blocked_sites()

    def is_site_blocked(self, url: str) -> bool:
        """Check if a site or its parent domain is blocked."""
        domain = self._extract_domain(url)
        parent_domain = self._get_parent_domain(url)
        current_time = time()
        
        # Check parent domain first
        if parent_domain in self.blocked_parent_domains:
            blocked_time = self.blocked_parent_domains[parent_domain]
            if current_time - blocked_time < self.block_duration:
                logger.info(f"Parent domain {parent_domain} is blocked")
                return True
            else:
                logger.info(f"Block expired for parent domain {parent_domain}")
                del self.blocked_parent_domains[parent_domain]
                self.parent_domain_counts[parent_domain].clear()
        
        # Check specific domain
        if domain in self.blocked_sites:
            blocked_time = self.blocked_sites[domain]
            if current_time - blocked_time < self.block_duration:
                return True
            else:
                del self.blocked_sites[domain]
                if parent_domain in self.parent_domain_counts:
                    self.parent_domain_counts[parent_domain].discard(domain)
        
        return False

    def get_blocked_domains_for_search(self) -> List[str]:
        """Get list of domains to exclude from search, prioritizing parent domains."""
        current_time = time()
        exclusions = []
        
        # Add parent domains first
        for domain, blocked_time in self.blocked_parent_domains.items():
            if current_time - blocked_time < self.block_duration:
                exclusions.append(domain)
        
        # Add individual domains that aren't part of blocked parent domains
        for domain, blocked_time in self.blocked_sites.items():
            if current_time - blocked_time < self.block_duration:
                parent = self._get_parent_domain(domain)
                if parent not in self.blocked_parent_domains:
                    exclusions.append(domain)
        
        return exclusions

    def get_blocked_sites_report(self) -> str:
        """Generate a report of currently blocked sites and parent domains."""
        current_time = time()
        report = []
        
        # Report blocked parent domains
        parent_domains = [domain for domain, blocked_time in self.blocked_parent_domains.items() 
                         if current_time - blocked_time < self.block_duration]
        if parent_domains:
            report.append("\nBlocked parent domains:")
            for domain in parent_domains:
                blocked_time = self.blocked_parent_domains[domain]
                remaining_hours = (self.block_duration - (current_time - blocked_time)) / 3600
                blocked_datetime = datetime.fromtimestamp(blocked_time).isoformat()
                report.append(f"- {domain}: blocked at {blocked_datetime}, {remaining_hours:.1f} hours remaining")
                report.append(f"  Affected subdomains: {len(self.parent_domain_counts[domain])}")
        
        # Report individual blocked sites
        individual_sites = [domain for domain, blocked_time in self.blocked_sites.items() 
                          if current_time - blocked_time < self.block_duration]
        if individual_sites:
            report.append("\nIndividually blocked sites:")
            for domain in individual_sites:
                blocked_time = self.blocked_sites[domain]
                remaining_hours = (self.block_duration - (current_time - blocked_time)) / 3600
                blocked_datetime = datetime.fromtimestamp(blocked_time).isoformat()
                report.append(f"- {domain}: blocked at {blocked_datetime}, {remaining_hours:.1f} hours remaining")
        
        return "\n".join(report) if report else "No sites currently blocked" 