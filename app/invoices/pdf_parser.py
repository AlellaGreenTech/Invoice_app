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

    # Common date formats
    DATE_PATTERNS = [
        r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b',  # MM/DD/YYYY or DD/MM/YYYY
        r'\b(\d{4}[/-]\d{1,2}[/-]\d{1,2})\b',    # YYYY-MM-DD
        r'\b([A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4})\b',  # Month DD, YYYY
        r'\b(\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4})\b',    # DD Month YYYY
    ]

    # Currency patterns
    CURRENCY_PATTERNS = [
        r'\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # $1,234.56
        r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*USD',  # 1,234.56 USD
        r'USD\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # USD 1,234.56
        r'€\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',    # €1,234.56
        r'£\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',    # £1,234.56
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

    def extract_total_amount(self, text):
        """
        Extract total amount from invoice text.

        Args:
            text: Invoice text

        Returns:
            tuple: (amount, currency) or (None, None)
        """
        # Look for "Total" or "Amount Due" patterns
        lines = text.split('\n')

        for line in lines:
            # Look for total indicators
            if re.search(r'(total|amount due|balance due|grand total)[\s:]*', line, re.IGNORECASE):
                # Try to extract amount from this line
                for pattern in self.CURRENCY_PATTERNS:
                    match = re.search(pattern, line)
                    if match:
                        amount_str = match.group(1).replace(',', '')
                        try:
                            amount = Decimal(amount_str)

                            # Detect currency
                            currency = 'USD'  # Default
                            if '€' in line:
                                currency = 'EUR'
                            elif '£' in line:
                                currency = 'GBP'
                            elif 'EUR' in line:
                                currency = 'EUR'
                            elif 'GBP' in line:
                                currency = 'GBP'

                            return amount, currency
                        except InvalidOperation:
                            continue

        # If no total found, try to find largest amount
        all_amounts = []
        for pattern in self.CURRENCY_PATTERNS:
            matches = re.findall(pattern, text)
            for match in matches:
                try:
                    amount = Decimal(match.replace(',', ''))
                    all_amounts.append(amount)
                except:
                    continue

        if all_amounts:
            # Return the largest amount (likely the total)
            return max(all_amounts), 'USD'

        return None, None

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
            total_amount, currency = self.extract_total_amount(text)
            invoice_number = self.extract_invoice_number(text)

            result = {
                'vendor_name': vendor_name,
                'invoice_date': invoice_date,
                'total_amount': total_amount,
                'currency': currency,
                'invoice_number': invoice_number,
                'raw_text': text,
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
                'invoice_number': None,
                'raw_text': None,
                'extraction_method': None,
                'success': False,
                'error': str(e)
            }
