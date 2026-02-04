"""PDF parser for extracting invoice data."""
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
import pdfplumber
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
from flask import current_app


class PDFParser:
    """Parser for extracting data from PDF invoices."""

    @staticmethod
    def clean_text(text):
        """Remove null bytes and other problematic characters from text."""
        if text is None:
            return None
        # Remove null bytes that PostgreSQL can't store
        text = text.replace('\x00', '')
        # Remove other control characters except newlines and tabs
        text = ''.join(char for char in text if char == '\n' or char == '\t' or (ord(char) >= 32 and ord(char) < 127) or ord(char) >= 160)
        return text

    # Common date formats
    DATE_PATTERNS = [
        r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b',  # MM/DD/YYYY or DD/MM/YYYY
        r'\b(\d{4}[/-]\d{1,2}[/-]\d{1,2})\b',    # YYYY-MM-DD
        r'\b([A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4})\b',  # Month DD, YYYY
        r'\b(\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4})\b',    # DD Month YYYY
    ]

    # Currency patterns with currency identification
    # Each pattern: (regex, currency, confidence)
    # EUR patterns are prioritized since this is a European-focused application
    CURRENCY_PATTERNS_WITH_CURRENCY = [
        # EUR patterns (highest confidence) - checked first
        (r'€\s*(\d{1,3}(?:[.\s]\d{3})*(?:,\d{2})?)', 'EUR', 1.0),  # €1.234,56 or €1 234,56
        (r'(\d{1,3}(?:[.\s]\d{3})*(?:,\d{2})?)\s*€', 'EUR', 1.0),  # 1.234,56€
        (r'€\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', 'EUR', 1.0),  # €1,234.56 (US format with € symbol)
        (r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*€', 'EUR', 1.0),  # 1,234.56€ (US format)
        (r'EUR\s*(\d{1,3}(?:[.\s]\d{3})*(?:,\d{2})?)', 'EUR', 0.95),  # EUR 1.234,56
        (r'(\d{1,3}(?:[.\s]\d{3})*(?:,\d{2})?)\s*EUR', 'EUR', 0.95),  # 1.234,56 EUR
        (r'EUR\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', 'EUR', 0.95),  # EUR 1,234.56
        (r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*EUR', 'EUR', 0.95),  # 1,234.56 EUR
        # European format without symbol (comma as decimal) - likely EUR
        (r'(\d{1,3}(?:\.\d{3})+,\d{2})', 'EUR', 0.85),  # 1.234,56 (European format, no symbol)
        # GBP patterns
        (r'£\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', 'GBP', 1.0),  # £1,234.56
        (r'GBP\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', 'GBP', 0.95),  # GBP 1,234.56
        (r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*GBP', 'GBP', 0.95),  # 1,234.56 GBP
        # USD patterns (lower confidence for bare $ since it's ambiguous)
        (r'US\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', 'USD', 1.0),  # US$1,234.56 (explicit)
        (r'USD\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', 'USD', 0.95),  # USD 1,234.56
        (r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*USD', 'USD', 0.95),  # 1,234.56 USD
        (r'\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', 'USD', 0.7),  # $1,234.56 (bare $ is ambiguous)
    ]

    # Legacy patterns for fallback - EUR patterns first
    CURRENCY_PATTERNS = [
        r'€\s*(\d{1,3}(?:[.\s]\d{3})*(?:,\d{2})?)',  # €1.234,56
        r'€\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',     # €1,234.56
        r'(\d{1,3}(?:\.\d{3})+,\d{2})',              # 1.234,56 (European format)
        r'£\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',    # £1,234.56
        r'\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',   # $1,234.56
        r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:USD|EUR|GBP)',  # 1,234.56 USD/EUR/GBP
    ]

    # Invoice number patterns
    INVOICE_NUMBER_PATTERNS = [
        r'Invoice\s*#?\s*:?\s*([A-Z0-9-]+)',
        r'Invoice\s+Number\s*:?\s*([A-Z0-9-]+)',
        r'INV\s*#?\s*:?\s*([A-Z0-9-]+)',
        r'Bill\s*#?\s*:?\s*([A-Z0-9-]+)',
    ]

    def __init__(self):
        """Initialize PDF parser."""
        pass

    def extract_text_from_pdf(self, pdf_path_or_bytes):
        """
        Extract text from PDF using pdfplumber.

        Args:
            pdf_path_or_bytes: Path to PDF file or bytes

        Returns:
            tuple: (text, method) where method is 'pdfplumber' or 'ocr'
        """
        try:
            # Try pdfplumber first
            if isinstance(pdf_path_or_bytes, bytes):
                import io
                pdf_file = io.BytesIO(pdf_path_or_bytes)
            else:
                pdf_file = pdf_path_or_bytes

            with pdfplumber.open(pdf_file) as pdf:
                text = ''
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + '\n'

            # If we got substantial text, return it
            if len(text.strip()) > 50:
                current_app.logger.info('Extracted text using pdfplumber')
                return text, 'pdfplumber'

            # Otherwise, fall back to OCR
            current_app.logger.info('Insufficient text from pdfplumber, trying OCR')
            return self.extract_text_with_ocr(pdf_path_or_bytes)

        except Exception as e:
            current_app.logger.error(f'pdfplumber extraction failed: {str(e)}')
            # Fall back to OCR
            return self.extract_text_with_ocr(pdf_path_or_bytes)

    def extract_text_with_ocr(self, pdf_path_or_bytes):
        """
        Extract text from PDF using OCR (Tesseract).

        Args:
            pdf_path_or_bytes: Path to PDF file or bytes

        Returns:
            tuple: (text, method) where method is 'ocr'
        """
        try:
            # Convert PDF to images
            if isinstance(pdf_path_or_bytes, bytes):
                images = convert_from_bytes(pdf_path_or_bytes)
            else:
                from pdf2image import convert_from_path
                images = convert_from_path(pdf_path_or_bytes)

            text = ''
            for i, image in enumerate(images):
                # Perform OCR on each page
                page_text = pytesseract.image_to_string(image)
                text += page_text + '\n'
                current_app.logger.debug(f'OCR extracted {len(page_text)} chars from page {i+1}')

            current_app.logger.info('Extracted text using OCR')
            return text, 'ocr'

        except Exception as e:
            current_app.logger.error(f'OCR extraction failed: {str(e)}')
            raise ValueError(f'Failed to extract text from PDF: {str(e)}')

    def extract_vendor_name(self, text):
        """
        Extract vendor name from invoice text.

        Args:
            text: Invoice text

        Returns:
            str or None: Vendor name
        """
        # Look for common vendor indicators
        lines = text.split('\n')

        # Try to find vendor in first few lines
        for i, line in enumerate(lines[:10]):
            line = line.strip()

            # Skip empty lines and common headers
            if not line or line.lower() in ['invoice', 'bill', 'receipt']:
                continue

            # Look for "From:" or "Vendor:" patterns
            if re.search(r'(from|vendor|billed by|seller):\s*(.+)', line, re.IGNORECASE):
                match = re.search(r'(from|vendor|billed by|seller):\s*(.+)', line, re.IGNORECASE)
                return match.group(2).strip()

            # First substantial line is often the vendor
            if len(line) > 3 and not re.match(r'^\d', line):
                return line

        return None

    def extract_invoice_date(self, text):
        """
        Extract invoice date from text.

        Args:
            text: Invoice text

        Returns:
            datetime.date or None: Invoice date
        """
        for pattern in self.DATE_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    # Try to parse the date
                    date = self.parse_date(match)
                    if date:
                        return date
                except:
                    continue

        return None

    def parse_date(self, date_string):
        """
        Parse date string into datetime.date.

        Args:
            date_string: Date string

        Returns:
            datetime.date or None
        """
        date_formats = [
            '%m/%d/%Y', '%m-%d-%Y', '%m/%d/%y', '%m-%d-%y',
            '%d/%m/%Y', '%d-%m-%Y', '%d/%m/%y', '%d-%m-%y',
            '%Y-%m-%d', '%Y/%m/%d',
            '%B %d, %Y', '%b %d, %Y',
            '%d %B %Y', '%d %b %Y',
        ]

        for fmt in date_formats:
            try:
                return datetime.strptime(date_string.strip(), fmt).date()
            except ValueError:
                continue

        return None

    def parse_european_number(self, amount_str):
        """
        Parse European number format (1.234,56) to Decimal.

        Args:
            amount_str: Amount string in European or US format

        Returns:
            Decimal or None
        """
        # Check if this looks like European format (comma as decimal separator)
        # European: 1.234,56 or 1 234,56
        # US: 1,234.56
        if ',' in amount_str and '.' in amount_str:
            # If comma comes after the last dot, it's European
            if amount_str.rfind(',') > amount_str.rfind('.'):
                # European format: replace dots (thousands) and comma (decimal)
                amount_str = amount_str.replace('.', '').replace(' ', '').replace(',', '.')
            else:
                # US format: just remove commas
                amount_str = amount_str.replace(',', '')
        elif ',' in amount_str:
            # Could be European decimal or US thousands
            # If comma is followed by exactly 2 digits at end, treat as decimal
            if re.match(r'.*,\d{2}$', amount_str):
                # European format with comma decimal
                amount_str = amount_str.replace('.', '').replace(' ', '').replace(',', '.')
            else:
                # US thousands separator
                amount_str = amount_str.replace(',', '')
        else:
            # Just dots or no separators - treat as US format
            amount_str = amount_str.replace(' ', '')

        try:
            return Decimal(amount_str)
        except InvalidOperation:
            return None

    def extract_total_amount(self, text):
        """
        Extract total amount from invoice text.

        Args:
            text: Invoice text

        Returns:
            dict: {amount, currency, currency_confidence} or {amount: None, currency: None, currency_confidence: 0.0}
        """
        result = {'amount': None, 'currency': None, 'currency_confidence': 0.0}

        # Look for "Total" or "Amount Due" patterns
        lines = text.split('\n')

        for line in lines:
            # Look for total indicators
            if re.search(r'(total|amount due|balance due|grand total|montant total|totaal|summe|totale)[\s:]*', line, re.IGNORECASE):
                # Try to extract amount with enhanced patterns
                for pattern, currency, confidence in self.CURRENCY_PATTERNS_WITH_CURRENCY:
                    match = re.search(pattern, line)
                    if match:
                        amount = self.parse_european_number(match.group(1))
                        if amount is not None:
                            return {'amount': amount, 'currency': currency, 'currency_confidence': confidence}

        # If no total found with enhanced patterns, try fallback
        for line in lines:
            if re.search(r'(total|amount due|balance due|grand total|montant total|totaal|summe|totale)[\s:]*', line, re.IGNORECASE):
                for pattern in self.CURRENCY_PATTERNS:
                    match = re.search(pattern, line)
                    if match:
                        amount = self.parse_european_number(match.group(1))
                        if amount is not None:
                            # Detect currency from line context - EUR biased
                            currency = 'EUR'  # Default to EUR
                            confidence = 0.5  # Lower confidence for fallback

                            # Check for explicit currency indicators (prioritize EUR)
                            if '€' in line:
                                currency = 'EUR'
                                confidence = 0.9
                            elif 'EUR' in line.upper():
                                currency = 'EUR'
                                confidence = 0.85
                            elif '£' in line:
                                currency = 'GBP'
                                confidence = 0.9
                            elif 'GBP' in line.upper():
                                currency = 'GBP'
                                confidence = 0.85
                            elif 'US$' in line or 'USD' in line.upper():
                                # Only USD if explicitly marked as US$ or USD
                                currency = 'USD'
                                confidence = 0.85
                            elif '$' in line:
                                # Bare $ is ambiguous - could be USD, CAD, AUD, etc.
                                # Keep as EUR default with low confidence
                                currency = 'EUR'
                                confidence = 0.4

                            return {'amount': amount, 'currency': currency, 'currency_confidence': confidence}

        # If no total found, try to find largest amount in whole text
        all_amounts = []
        for pattern, currency, confidence in self.CURRENCY_PATTERNS_WITH_CURRENCY:
            matches = re.finditer(pattern, text)
            for match in matches:
                amount = self.parse_european_number(match.group(1))
                if amount is not None:
                    all_amounts.append((amount, currency, confidence))

        if all_amounts:
            # Return the largest amount (likely the total) with lower confidence
            best = max(all_amounts, key=lambda x: x[0])
            return {'amount': best[0], 'currency': best[1], 'currency_confidence': best[2] * 0.7}

        # Last resort: look for any number that looks like a total
        for pattern in self.CURRENCY_PATTERNS:
            matches = re.findall(pattern, text)
            for match in matches:
                amount = self.parse_european_number(match)
                if amount is not None:
                    all_amounts.append(amount)

        if all_amounts:
            return {'amount': max(all_amounts), 'currency': 'EUR', 'currency_confidence': 0.3}

        return result

    def extract_invoice_number(self, text):
        """
        Extract invoice number from text.

        Args:
            text: Invoice text

        Returns:
            str or None: Invoice number
        """
        for pattern in self.INVOICE_NUMBER_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return None

    def parse_invoice(self, pdf_path_or_bytes):
        """
        Parse invoice PDF and extract all relevant data.

        Args:
            pdf_path_or_bytes: Path to PDF file or bytes

        Returns:
            dict: Extracted invoice data
        """
        try:
            # Extract text
            text, extraction_method = self.extract_text_from_pdf(pdf_path_or_bytes)

            # Extract fields
            vendor_name = self.extract_vendor_name(text)
            invoice_date = self.extract_invoice_date(text)
            amount_data = self.extract_total_amount(text)
            invoice_number = self.extract_invoice_number(text)

            result = {
                'vendor_name': self.clean_text(vendor_name),
                'invoice_date': invoice_date,
                'total_amount': amount_data['amount'],
                'currency': amount_data['currency'],
                'currency_confidence': amount_data['currency_confidence'],
                'invoice_number': self.clean_text(invoice_number),
                'raw_text': self.clean_text(text),
                'extraction_method': extraction_method,
                'success': True,
                'error': None
            }

            current_app.logger.info(f'Successfully parsed invoice: {vendor_name}')

            return result

        except Exception as e:
            current_app.logger.error(f'Failed to parse invoice: {str(e)}')
            return {
                'vendor_name': None,
                'invoice_date': None,
                'total_amount': None,
                'currency': None,
                'currency_confidence': 0.0,
                'invoice_number': None,
                'raw_text': None,
                'extraction_method': None,
                'success': False,
                'error': str(e)
            }
