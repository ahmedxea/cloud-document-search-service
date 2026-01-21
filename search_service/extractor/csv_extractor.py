"""
CSV file extractor.
Converts CSV rows to searchable text format.
"""
import csv
import io
import logging
from .base_extractor import BaseExtractor

logger = logging.getLogger(__name__)


class CSVExtractor(BaseExtractor):
    """Extractor for CSV files"""
    
    def can_extract(self, mime_type: str, filename: str) -> bool:
        """Check if file is a CSV file"""
        # Check MIME type
        if mime_type in self.get_supported_mime_types():
            return True
        
        # Check file extension
        filename_lower = filename.lower()
        return any(filename_lower.endswith(ext) for ext in self.get_supported_extensions())
    
    def extract_text(self, content: bytes, filename: str) -> str:
        """
        Extract text from CSV file.
        Converts to a searchable format: headers and all row values.
        """
        try:
            # Decode bytes to string
            text_content = content.decode('utf-8')
            
            # Parse CSV
            csv_reader = csv.reader(io.StringIO(text_content))
            
            rows = list(csv_reader)
            if not rows:
                logger.warning(f"Empty CSV file: {filename}")
                return ""
            
            # Extract header (first row)
            header = rows[0] if rows else []
            
            # Build searchable text
            # Format: "header1: value1, header2: value2, ..."
            lines = []
            
            # Add headers as searchable terms
            lines.append("Headers: " + ", ".join(header))
            
            # Add each row's data
            for i, row in enumerate(rows[1:], start=1):
                if row:  # Skip empty rows
                    row_text = " | ".join(str(cell) for cell in row if cell)
                    lines.append(f"Row {i}: {row_text}")
            
            extracted_text = "\n".join(lines)
            logger.debug(f"Extracted {len(extracted_text)} chars from CSV {filename} ({len(rows)} rows)")
            
            return extracted_text.strip()
            
        except UnicodeDecodeError:
            # Try latin-1 encoding as fallback
            try:
                text_content = content.decode('latin-1')
                csv_reader = csv.reader(io.StringIO(text_content))
                rows = list(csv_reader)
                
                lines = []
                for i, row in enumerate(rows):
                    if row:
                        lines.append(" | ".join(str(cell) for cell in row if cell))
                
                extracted_text = "\n".join(lines)
                logger.warning(f"Used latin-1 fallback for CSV {filename}")
                return extracted_text.strip()
                
            except Exception as e:
                logger.error(f"Failed to parse CSV {filename}: {e}")
                raise ValueError(f"Could not parse CSV file {filename}: {e}")
        
        except Exception as e:
            logger.error(f"Error extracting from CSV {filename}: {e}")
            raise ValueError(f"Could not extract text from CSV {filename}: {e}")
    
    def get_supported_mime_types(self) -> list[str]:
        """Return supported MIME types for CSV files"""
        return [
            'text/csv',
            'application/csv',
            'text/comma-separated-values',
            'application/vnd.ms-excel',  # Sometimes CSV files have this
        ]
    
    def get_supported_extensions(self) -> list[str]:
        """Return supported file extensions"""
        return ['.csv']
