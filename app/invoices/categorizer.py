"""AI-powered invoice categorization using Claude API."""
import anthropic
from flask import current_app


class InvoiceCategorizer:
    """Categorizer for invoices using Claude API."""

    # Default categories
    DEFAULT_CATEGORIES = [
        'Office Supplies',
        'Travel',
        'Software & Technology',
        'Professional Services',
        'Utilities',
        'Marketing & Advertising',
        'Equipment & Hardware',
        'Rent & Facilities',
        'Insurance',
        'Legal & Compliance',
        'Training & Education',
        'Meals & Entertainment',
        'Telecommunications',
        'Shipping & Delivery',
        'Maintenance & Repairs',
        'Other'
    ]

    # Keyword-based fallback rules
    CATEGORY_KEYWORDS = {
        'Office Supplies': ['staples', 'office depot', 'paper', 'pens', 'supplies', 'stationery'],
        'Travel': ['airline', 'hotel', 'uber', 'lyft', 'rental car', 'airbnb', 'expedia', 'booking'],
        'Software & Technology': ['software', 'saas', 'cloud', 'hosting', 'domain', 'aws', 'azure', 'github', 'adobe'],
        'Professional Services': ['consulting', 'legal', 'accounting', 'audit', 'advisory'],
        'Utilities': ['electric', 'water', 'gas', 'utility', 'power', 'energy'],
        'Marketing & Advertising': ['google ads', 'facebook ads', 'marketing', 'advertising', 'promotion'],
        'Equipment & Hardware': ['computer', 'laptop', 'monitor', 'printer', 'equipment', 'hardware'],
        'Telecommunications': ['phone', 'internet', 'telecom', 'verizon', 'at&t', 'comcast'],
        'Shipping & Delivery': ['fedex', 'ups', 'usps', 'dhl', 'shipping', 'freight'],
        'Meals & Entertainment': ['restaurant', 'catering', 'food', 'meal', 'dining'],
    }

    def __init__(self):
        """Initialize categorizer with Claude API."""
        self.api_key = current_app.config.get('ANTHROPIC_API_KEY')
        if not self.api_key:
            current_app.logger.warning('Anthropic API key not configured')
            self.client = None
        else:
            self.client = anthropic.Anthropic(api_key=self.api_key)

    def categorize_invoice(self, invoice_data):
        """
        Categorize an invoice using Claude API.

        Args:
            invoice_data: Dictionary with vendor_name, invoice_date, total_amount, raw_text

        Returns:
            dict: {
                'category': str,
                'confidence': float (0-1),
                'reasoning': str
            }
        """
        # If Claude API is not available, use fallback
        if not self.client:
            return self.categorize_with_rules(invoice_data)

        try:
            # Build prompt for Claude
            prompt = self._build_categorization_prompt(invoice_data)

            # Call Claude API
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=500,
                temperature=0,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Parse response
            response_text = message.content[0].text
            result = self._parse_categorization_response(response_text)

            current_app.logger.info(
                f'Categorized invoice as "{result["category"]}" '
                f'with {result["confidence"]:.0%} confidence'
            )

            return result

        except Exception as e:
            current_app.logger.error(f'Claude API categorization failed: {str(e)}')
            # Fall back to rule-based categorization
            return self.categorize_with_rules(invoice_data)

    def _build_categorization_prompt(self, invoice_data):
        """
        Build prompt for Claude API.

        Args:
            invoice_data: Invoice data dictionary

        Returns:
            str: Formatted prompt
        """
        vendor = invoice_data.get('vendor_name', 'Unknown')
        amount = invoice_data.get('total_amount', 'Unknown')
        currency = invoice_data.get('currency', 'USD')
        raw_text = invoice_data.get('raw_text', '')

        # Truncate raw text if too long
        if len(raw_text) > 2000:
            raw_text = raw_text[:2000] + '...'

        categories_list = '\n'.join([f'- {cat}' for cat in self.DEFAULT_CATEGORIES])

        prompt = f"""You are an expert accountant categorizing business invoices.

Analyze this invoice and categorize it into ONE of the following categories:

{categories_list}

Invoice Information:
- Vendor: {vendor}
- Amount: {currency} {amount}

Invoice Text:
{raw_text}

Respond in the following format:
Category: [category name]
Confidence: [0-100]
Reasoning: [brief explanation]

Choose the most specific and accurate category. If uncertain, use "Other"."""

        return prompt

    def _parse_categorization_response(self, response_text):
        """
        Parse Claude's response.

        Args:
            response_text: Response from Claude

        Returns:
            dict: Parsed categorization result
        """
        import re

        # Extract category
        category_match = re.search(r'Category:\s*(.+)', response_text, re.IGNORECASE)
        category = category_match.group(1).strip() if category_match else 'Other'

        # Extract confidence
        confidence_match = re.search(r'Confidence:\s*(\d+)', response_text, re.IGNORECASE)
        confidence = int(confidence_match.group(1)) / 100 if confidence_match else 0.5

        # Extract reasoning
        reasoning_match = re.search(r'Reasoning:\s*(.+)', response_text, re.IGNORECASE | re.DOTALL)
        reasoning = reasoning_match.group(1).strip() if reasoning_match else 'AI categorization'

        # Validate category is in our list
        if category not in self.DEFAULT_CATEGORIES:
            # Try to find closest match
            category_lower = category.lower()
            for valid_category in self.DEFAULT_CATEGORIES:
                if valid_category.lower() in category_lower or category_lower in valid_category.lower():
                    category = valid_category
                    break
            else:
                category = 'Other'

        return {
            'category': category,
            'confidence': confidence,
            'reasoning': reasoning
        }

    def categorize_with_rules(self, invoice_data):
        """
        Fallback rule-based categorization using keywords.

        Args:
            invoice_data: Invoice data dictionary

        Returns:
            dict: Categorization result
        """
        vendor = (invoice_data.get('vendor_name') or '').lower()
        raw_text = (invoice_data.get('raw_text') or '').lower()

        # Combine vendor and text for matching
        search_text = f"{vendor} {raw_text}"

        # Check each category's keywords
        best_match = None
        best_score = 0

        for category, keywords in self.CATEGORY_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword.lower() in search_text)
            if score > best_score:
                best_score = score
                best_match = category

        if best_match and best_score > 0:
            confidence = min(0.7, 0.4 + (best_score * 0.1))  # Max 70% confidence for rules
            return {
                'category': best_match,
                'confidence': confidence,
                'reasoning': f'Rule-based match ({best_score} keywords)'
            }

        # Default to Other
        return {
            'category': 'Other',
            'confidence': 0.3,
            'reasoning': 'No clear category match found'
        }

    def batch_categorize(self, invoices_data):
        """
        Categorize multiple invoices.

        Args:
            invoices_data: List of invoice data dictionaries

        Returns:
            list: List of categorization results
        """
        results = []
        for invoice_data in invoices_data:
            result = self.categorize_invoice(invoice_data)
            results.append(result)

        return results

    @staticmethod
    def get_default_categories():
        """
        Get list of default categories.

        Returns:
            list: Default category names
        """
        return InvoiceCategorizer.DEFAULT_CATEGORIES.copy()
