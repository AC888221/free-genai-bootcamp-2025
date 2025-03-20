import json
import logging
import os
from time import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Set, List
from collections import defaultdict
import tldextract

logger = logging.getLogger(__name__)

class ExcludedSitesTracker:
    def __init__(self, exclusion_duration_hours: int = 24, parent_exclusion_threshold: int = 3):
        self.exclusion_duration = exclusion_duration_hours * 3600
        self.parent_exclusion_threshold = parent_exclusion_threshold
        self.excluded_sites_file = "excluded_sites.json"
        self.excluded_sites: Dict[str, float] = {}
        self.parent_domain_counts: Dict[str, Set[str]] = defaultdict(set)
        self.excluded_parent_domains: Dict[str, float] = {}
        self.load_excluded_sites()

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

    def load_excluded_sites(self):
        """Load excluded sites from JSON file."""
        try:
            if os.path.exists(self.excluded_sites_file):
                with open(self.excluded_sites_file, 'r') as f:
                    data = json.load(f)
                    self.excluded_sites = data.get('sites', {})
                    self.excluded_parent_domains = data.get('parent_domains', {})
                logger.info(f"Loaded {len(self.excluded_sites)} excluded sites and {len(self.excluded_parent_domains)} parent domains")
                
                # Rebuild parent domain counts
                for domain in self.excluded_sites:
                    parent = self._get_parent_domain(domain)
                    if parent:
                        self.parent_domain_counts[parent].add(domain)
        except Exception as e:
            logger.error(f"Error loading excluded sites: {str(e)}")
            self.excluded_sites = {}
            self.excluded_parent_domains = {}

    def save_excluded_sites(self):
        """Save excluded sites to JSON file."""
        try:
            data = {
                'sites': self.excluded_sites,
                'parent_domains': self.excluded_parent_domains
            }
            with open(self.excluded_sites_file, 'w') as f:
                json.dump(data, f)
            logger.info(f"Saved {len(self.excluded_sites)} excluded sites and {len(self.excluded_parent_domains)} parent domains")
        except Exception as e:
            logger.error(f"Error saving excluded sites: {str(e)}")

    def _get_parent_domain(self, url: str) -> str:
        """Extract parent domain from URL using tldextract."""
        extracted = tldextract.extract(url)
        return f"{extracted.domain}.{extracted.suffix}"

    def add_excluded_site(self, url: str):
        """Add a site to the excluded list and check parent domain patterns."""
        domain = self._extract_domain(url)
        parent_domain = self._get_parent_domain(url)
        
        # Add to excluded sites
        self.excluded_sites[domain] = time()
        logger.warning(f"Added {domain} to excluded sites at {datetime.now().isoformat()}")
        
        # Track parent domain
        if parent_domain:
            self.parent_domain_counts[parent_domain].add(domain)
            
            # Check if parent domain should be excluded
            if len(self.parent_domain_counts[parent_domain]) >= self.parent_exclusion_threshold:
                if parent_domain not in self.excluded_parent_domains:
                    self.excluded_parent_domains[parent_domain] = time()
                    logger.warning(f"Excluding parent domain {parent_domain} due to {len(self.parent_domain_counts[parent_domain])} excluded subdomains")
        
        self.save_excluded_sites()

    def is_site_excluded(self, url: str) -> bool:
        """Check if a site or its parent domain is excluded."""
        domain = self._extract_domain(url)
        parent_domain = self._get_parent_domain(url)
        current_time = time()
        
        # Check parent domain first
        if parent_domain in self.excluded_parent_domains:
            excluded_time = self.excluded_parent_domains[parent_domain]
            if current_time - excluded_time < self.exclusion_duration:
                logger.info(f"Parent domain {parent_domain} is excluded")
                return True
            else:
                logger.info(f"Exclusion expired for parent domain {parent_domain}")
                del self.excluded_parent_domains[parent_domain]
                self.parent_domain_counts[parent_domain].clear()
        
        # Check specific domain
        if domain in self.excluded_sites:
            excluded_time = self.excluded_sites[domain]
            if current_time - excluded_time < self.exclusion_duration:
                return True
            else:
                del self.excluded_sites[domain]
                if parent_domain in self.parent_domain_counts:
                    self.parent_domain_counts[parent_domain].discard(domain)
        
        return False

    def get_excluded_domains_for_search(self) -> List[str]:
        """Get list of domains to exclude from search, prioritizing parent domains."""
        current_time = time()
        exclusions = []
        
        # Add parent domains first
        for domain, excluded_time in self.excluded_parent_domains.items():
            if current_time - excluded_time < self.exclusion_duration:
                exclusions.append(domain)
        
        # Add individual domains that aren't part of excluded parent domains
        for domain, excluded_time in self.excluded_sites.items():
            if current_time - excluded_time < self.exclusion_duration:
                parent = self._get_parent_domain(domain)
                if parent not in self.excluded_parent_domains:
                    exclusions.append(domain)
        
        return exclusions

    def get_excluded_sites_report(self) -> str:
        """Generate a report of currently excluded sites and parent domains."""
        current_time = time()
        report = []
        
        # Report excluded parent domains
        parent_domains = [domain for domain, excluded_time in self.excluded_parent_domains.items() 
                         if current_time - excluded_time < self.exclusion_duration]
        if parent_domains:
            report.append("\nExcluded parent domains:")
            for domain in parent_domains:
                excluded_time = self.excluded_parent_domains[domain]
                remaining_hours = (self.exclusion_duration - (current_time - excluded_time)) / 3600
                excluded_datetime = datetime.fromtimestamp(excluded_time).isoformat()
                report.append(f"- {domain}: excluded at {excluded_datetime}, {remaining_hours:.1f} hours remaining")
                report.append(f"  Affected subdomains: {len(self.parent_domain_counts[domain])}")
        
        # Report individually excluded sites
        individual_sites = [domain for domain, excluded_time in self.excluded_sites.items() 
                          if current_time - excluded_time < self.exclusion_duration]
        if individual_sites:
            report.append("\nIndividually excluded sites:")
            for domain in individual_sites:
                excluded_time = self.excluded_sites[domain]
                remaining_hours = (self.exclusion_duration - (current_time - excluded_time)) / 3600
                excluded_datetime = datetime.fromtimestamp(excluded_time).isoformat()
                report.append(f"- {domain}: excluded at {excluded_datetime}, {remaining_hours:.1f} hours remaining")
        
        return "\n".join(report) if report else "No sites currently excluded" 