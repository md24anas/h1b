"""
AI-Powered Wage Level Predictor
Uses OFLC wage data and LLM to predict appropriate wage levels for jobs
"""
import os
import csv
import logging
import re
from typing import Dict, Optional, List, Tuple
from difflib import get_close_matches

logger = logging.getLogger(__name__)

class WageLevelPredictor:
    """Predicts wage levels using OFLC data and AI"""
    
    def __init__(self):
        self.wage_data = {}  # {state_abbr: {soc_code: {level1, level2, level3, level4}}}
        self.soc_titles = {}  # {soc_code: title}
        self.soc_descriptions = {}  # {soc_code: description}
        self.geography = {}  # {area_code: {name, state_abbr}}
        self.loaded = False
        
    def load_data(self, data_dir: str = "/app/backend/OFLC_Wages_2025-26_Updated"):
        """Load OFLC wage data"""
        if self.loaded:
            return
            
        try:
            logger.info("Loading OFLC wage data...")
            
            # Load SOC titles and descriptions
            soc_file = os.path.join(data_dir, "oes_soc_occs.csv")
            if os.path.exists(soc_file):
                with open(soc_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        soc_code = row.get('soccode', '').strip()
                        if soc_code:
                            self.soc_titles[soc_code] = row.get('Title', '').strip()
                            self.soc_descriptions[soc_code] = row.get('Description', '').strip()
                logger.info(f"Loaded {len(self.soc_titles)} SOC occupations")
            
            # Load geography data
            geo_file = os.path.join(data_dir, "Geography.csv")
            if os.path.exists(geo_file):
                with open(geo_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        area = row.get('Area', '').strip()
                        state_ab = row.get('StateAb', '').strip()
                        if area and state_ab:
                            self.geography[area] = {
                                'name': row.get('AreaName', '').strip(),
                                'state_abbr': state_ab
                            }
                logger.info(f"Loaded {len(self.geography)} geographic areas")
            
            # Load wage data (ALC_Export.csv - most comprehensive)
            wage_file = os.path.join(data_dir, "ALC_Export.csv")
            if os.path.exists(wage_file):
                with open(wage_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        area = row.get('Area', '').strip()
                        soc_code = row.get('SocCode', '').strip()
                        
                        # Get state from geography
                        geo_info = self.geography.get(area, {})
                        state_abbr = geo_info.get('state_abbr', 'US')
                        
                        if not state_abbr or not soc_code:
                            continue
                        
                        # Parse wage levels (hourly)
                        try:
                            level1 = float(row.get('Level1', 0))
                            level2 = float(row.get('Level2', 0))
                            level3 = float(row.get('Level3', 0))
                            level4 = float(row.get('Level4', 0))
                            
                            # Store by state and SOC code
                            if state_abbr not in self.wage_data:
                                self.wage_data[state_abbr] = {}
                            
                            if soc_code not in self.wage_data[state_abbr]:
                                self.wage_data[state_abbr][soc_code] = {
                                    'level1': level1 * 2080,  # Convert to annual
                                    'level2': level2 * 2080,
                                    'level3': level3 * 2080,
                                    'level4': level4 * 2080
                                }
                        except (ValueError, TypeError):
                            continue
                
                logger.info(f"Loaded wage data for {len(self.wage_data)} states")
            
            self.loaded = True
            logger.info("OFLC wage data loaded successfully!")
            
        except Exception as e:
            logger.error(f"Error loading OFLC data: {e}")
            self.loaded = False
    
    def find_soc_code_by_title(self, job_title: str) -> Optional[str]:
        """Find SOC code by job title using fuzzy matching"""
        if not job_title or not self.soc_titles:
            return None
        
        job_title_lower = job_title.lower()
        
        # First try exact match
        for soc_code, title in self.soc_titles.items():
            if title.lower() == job_title_lower:
                return soc_code
        
        # Try partial matches
        for soc_code, title in self.soc_titles.items():
            title_lower = title.lower()
            # Check if key terms match
            if any(word in title_lower for word in job_title_lower.split() if len(word) > 3):
                if any(word in job_title_lower for word in title_lower.split() if len(word) > 3):
                    return soc_code
        
        # Use fuzzy matching as last resort
        soc_titles_list = list(self.soc_titles.values())
        matches = get_close_matches(job_title, soc_titles_list, n=1, cutoff=0.6)
        if matches:
            # Find SOC code for the match
            for soc_code, title in self.soc_titles.items():
                if title == matches[0]:
                    return soc_code
        
        # Common tech job mappings
        tech_mappings = {
            'software engineer': '15-1252',
            'software developer': '15-1252',
            'web developer': '15-1254',
            'data scientist': '15-2051',
            'data analyst': '15-2051',
            'database administrator': '15-1242',
            'network engineer': '15-1244',
            'systems administrator': '15-1244',
            'devops': '15-1244',
            'product manager': '11-2021',
            'project manager': '11-9199',
        }
        
        for key, soc in tech_mappings.items():
            if key in job_title_lower:
                return soc
        
        return None
    
    def get_wage_levels_for_job(self, job_title: str, state: str) -> Optional[Dict[str, float]]:
        """Get wage levels for a job title and state"""
        if not self.loaded:
            self.load_data()
        
        # Find SOC code
        soc_code = self.find_soc_code_by_title(job_title)
        if not soc_code:
            logger.debug(f"No SOC code found for: {job_title}")
            return None
        
        # Get wage data for state
        state_wages = self.wage_data.get(state, self.wage_data.get('US', {}))
        if soc_code not in state_wages:
            # Try national average if state-specific not available
            state_wages = self.wage_data.get('US', {})
        
        if soc_code in state_wages:
            return state_wages[soc_code]
        
        return None
    
    def predict_wage_level(self, job_title: str, state: str, salary: float) -> int:
        """
        Predict wage level (1-4) based on job title, location, and salary
        
        Returns:
            1-4: Predicted wage level
            2: Default if unable to determine
        """
        if not salary or salary <= 0:
            return 2  # Default to level 2
        
        # Get OFLC wage levels for this job/location
        wage_levels = self.get_wage_levels_for_job(job_title, state)
        
        if not wage_levels:
            # Fallback: use general tech salary ranges
            if salary < 80000:
                return 1
            elif salary < 120000:
                return 2
            elif salary < 160000:
                return 3
            else:
                return 4
        
        # Compare salary to OFLC levels
        level1 = wage_levels.get('level1', 0)
        level2 = wage_levels.get('level2', 0)
        level3 = wage_levels.get('level3', 0)
        level4 = wage_levels.get('level4', 0)
        
        # Determine which level the salary falls into
        if salary < level1:
            return 1
        elif salary < level2:
            return 1
        elif salary < level3:
            return 2
        elif salary < level4:
            return 3
        else:
            return 4
    
    def get_suggested_salary_range(self, job_title: str, state: str, level: int = 2) -> Tuple[float, float]:
        """Get suggested salary range for a job/location/level"""
        wage_levels = self.get_wage_levels_for_job(job_title, state)
        
        if not wage_levels:
            # Default tech ranges by level
            ranges = {
                1: (60000, 90000),
                2: (90000, 130000),
                3: (130000, 180000),
                4: (180000, 250000)
            }
            return ranges.get(level, (90000, 130000))
        
        # Get the specific level's wage
        level_key = f'level{level}'
        wage = wage_levels.get(level_key, 0)
        
        # Return range: -10% to +10% of the level wage
        return (wage * 0.9, wage * 1.1)

# Global instance
wage_predictor = WageLevelPredictor()
