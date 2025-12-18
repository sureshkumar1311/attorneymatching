import pandas as pd
from typing import List, Dict, Any, Tuple
import re
from config import settings

class ExcelValidator:
    
    @staticmethod
    def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
        """Normalize column names to lowercase and strip whitespace"""
        df.columns = df.columns.str.lower().str.strip()
        return df
    
    @staticmethod
    def validate_attorney_excel(file_path: str) -> Tuple[bool, List[Dict[str, Any]], List[str]]:
        """
        Validates attorney Excel file and returns parsed data
        Returns: (is_valid, parsed_attorneys, error_messages)
        
        RELAXED VALIDATION:
        - Only name, seniority, years_of_experience are REQUIRED
        - Practice areas are OPTIONAL (will create empty array if none)
        - Email is OPTIONAL (will use generated email if missing)
        - Column names are case-insensitive
        - Empty/NULL values are allowed for optional fields
        """
        errors = []
        attorneys = []
        
        try:
            df = pd.read_excel(file_path)
        except Exception as e:
            return False, [], [f"Failed to read Excel file: {str(e)}"]
        
        # Normalize column names (lowercase, strip whitespace)
        df = ExcelValidator.normalize_column_names(df)
        
        # Check ONLY required columns (relaxed)
        required_cols = ['name', 'seniority', 'years_of_experience']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            return False, [], [f"Missing required columns: {', '.join(missing_cols)}"]
        
        # Validate each row
        for idx, row in df.iterrows():
            row_errors = []
            
            # Name validation (REQUIRED)
            if pd.isna(row['name']) or len(str(row['name']).strip()) == 0:
                row_errors.append(f"Row {idx+2}: Name is required")
                continue  # Skip this row entirely if no name
            
            name = str(row['name']).strip()
            if len(name) > settings.MAX_NAME_LENGTH:
                row_errors.append(f"Row {idx+2}: Name exceeds {settings.MAX_NAME_LENGTH} characters")
                continue
            
            # Email validation (OPTIONAL - generate if missing)
            if 'email' in df.columns and not pd.isna(row['email']):
                email = str(row['email']).strip()
                if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
                    row_errors.append(f"Row {idx+2}: Invalid email format")
                    continue
            else:
                # Generate email from name if missing
                email_name = name.lower().replace(' ', '.')
                email = f"{email_name}@lawfirm.com"
            
            # Seniority validation (REQUIRED)
            if pd.isna(row['seniority']):
                row_errors.append(f"Row {idx+2}: Seniority is required")
                continue
            
            seniority = str(row['seniority']).strip()
            # Case-insensitive seniority matching
            seniority_lower = seniority.lower()
            seniority_map = {
                'associate': 'Associate',
                'senior associate': 'Senior Associate',
                'partner': 'Partner',
                'senior partner': 'Senior Partner'
            }
            
            if seniority_lower in seniority_map:
                seniority = seniority_map[seniority_lower]
            elif seniority not in settings.SENIORITY_LEVELS:
                row_errors.append(f"Row {idx+2}: Invalid seniority level. Use: Associate, Senior Associate, Partner, or Senior Partner")
                continue
            
            # Years of experience validation (REQUIRED)
            try:
                years_exp = int(row['years_of_experience'])
                if years_exp < 0 or years_exp > settings.MAX_YEARS_EXPERIENCE:
                    row_errors.append(f"Row {idx+2}: Years of experience must be between 0 and {settings.MAX_YEARS_EXPERIENCE}")
                    continue
            except (ValueError, TypeError):
                row_errors.append(f"Row {idx+2}: Invalid years_of_experience (must be a number)")
                continue
            
            # Parse practice areas (OPTIONAL - can be empty)
            practice_areas = []
            for i in range(1, settings.MAX_PRACTICE_AREAS + 1):
                area_col = f'practice_area_{i}'
                prof_col = f'proficiency_{i}'
                years_col = f'years_in_practice_{i}'
                
                # Check if practice area column exists and has value
                if area_col in df.columns and not pd.isna(row.get(area_col)):
                    area_value = str(row[area_col]).strip()
                    if area_value:  # Only add if not empty string
                        try:
                            # Get proficiency (default to Intermediate if missing)
                            if prof_col in df.columns and not pd.isna(row.get(prof_col)):
                                proficiency = str(row[prof_col]).strip()
                                # Case-insensitive proficiency matching
                                proficiency_lower = proficiency.lower()
                                proficiency_map = {
                                    'beginner': 'Beginner',
                                    'intermediate': 'Intermediate',
                                    'advanced': 'Advanced',
                                    'expert': 'Expert'
                                }
                                if proficiency_lower in proficiency_map:
                                    proficiency = proficiency_map[proficiency_lower]
                                elif proficiency not in settings.PROFICIENCY_LEVELS:
                                    proficiency = 'Intermediate'  # Default
                            else:
                                proficiency = 'Intermediate'
                            
                            # Get years in practice (default to 0 if missing)
                            if years_col in df.columns and not pd.isna(row.get(years_col)):
                                years_in_practice = int(row[years_col])
                            else:
                                years_in_practice = 0
                            
                            # Validate years in practice doesn't exceed total experience
                            if years_in_practice > years_exp:
                                years_in_practice = years_exp  # Cap at total experience
                            
                            practice_areas.append({
                                "area": area_value,
                                "proficiency": proficiency,
                                "years_in_practice": years_in_practice
                            })
                        except (ValueError, TypeError):
                            # Skip invalid practice area data
                            continue
            
            # NO LONGER REQUIRE practice areas - allow empty array
            # If no practice areas, just create attorney without them
            
            if row_errors:
                errors.extend(row_errors)
            else:
                attorneys.append({
                    "name": name,
                    "email": email,
                    "seniority": seniority,
                    "years_of_experience": years_exp,
                    "practice_areas": practice_areas  # Can be empty array
                })
        
        is_valid = len(errors) == 0
        return is_valid, attorneys, errors
    
    @staticmethod
    def validate_public_data_excel(file_path: str) -> Tuple[bool, List[Dict[str, Any]], List[str]]:
        """
        Validates public data Excel file (temporary seeding)
        Returns: (is_valid, parsed_sources, error_messages)
        
        RELAXED VALIDATION:
        - Only title and url are REQUIRED
        - All other fields are OPTIONAL
        - Column names are case-insensitive
        """
        errors = []
        public_sources = []
        
        try:
            df = pd.read_excel(file_path)
        except Exception as e:
            return False, [], [f"Failed to read Excel file: {str(e)}"]
        
        # Normalize column names
        df = ExcelValidator.normalize_column_names(df)
        
        required_cols = ['title', 'url']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            return False, [], [f"Missing required columns: {', '.join(missing_cols)}"]
        
        for idx, row in df.iterrows():
            if pd.isna(row['title']) or pd.isna(row['url']):
                errors.append(f"Row {idx+2}: Title and URL are required")
                continue
            
            title = str(row['title']).strip()
            url = str(row['url']).strip()
            
            if not title:
                errors.append(f"Row {idx+2}: Title cannot be empty")
                continue
                
            if not re.match(r'^https?://.+', url):
                errors.append(f"Row {idx+2}: Invalid URL format (must start with http:// or https://)")
                continue
            
            source_data = {
                "title": title,
                "url": url
            }
            
            # Optional fields - add only if present and not empty
            optional_fields = ['risk_area', 'summary', 'source', 'published_date', 
                             'jurisdiction', 'impact_level']
            for field in optional_fields:
                if field in df.columns and not pd.isna(row[field]):
                    value = str(row[field]).strip()
                    if value:  # Only add if not empty string
                        source_data[field] = value
            
            public_sources.append(source_data)
        
        is_valid = len(errors) == 0
        return is_valid, public_sources, errors
