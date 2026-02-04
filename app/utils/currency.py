"""Currency conversion service."""
from decimal import Decimal, ROUND_HALF_UP


class CurrencyConverter:
    """Currency converter with static exchange rates."""

    # Static exchange rates (approximate, for consistent reporting)
    # Rates are relative to EUR as the base
    RATES_TO_EUR = {
        'EUR': Decimal('1.00'),
        'USD': Decimal('0.92'),   # 1 USD = 0.92 EUR
        'GBP': Decimal('1.17'),   # 1 GBP = 1.17 EUR
    }

    # Precomputed cross rates for efficiency
    STATIC_RATES = {
        ('EUR', 'EUR'): Decimal('1.00'),
        ('EUR', 'USD'): Decimal('1.09'),
        ('EUR', 'GBP'): Decimal('0.85'),
        ('USD', 'EUR'): Decimal('0.92'),
        ('USD', 'USD'): Decimal('1.00'),
        ('USD', 'GBP'): Decimal('0.78'),
        ('GBP', 'EUR'): Decimal('1.17'),
        ('GBP', 'USD'): Decimal('1.28'),
        ('GBP', 'GBP'): Decimal('1.00'),
    }

    @classmethod
    def convert(cls, amount, from_currency, to_currency):
        """
        Convert amount from one currency to another.

        Args:
            amount: Amount to convert (Decimal or float)
            from_currency: Source currency code (EUR, USD, GBP)
            to_currency: Target currency code (EUR, USD, GBP)

        Returns:
            Decimal: Converted amount rounded to 2 decimal places
        """
        if amount is None:
            return None

        if not isinstance(amount, Decimal):
            amount = Decimal(str(amount))

        # Same currency, no conversion needed
        if from_currency == to_currency:
            return amount

        # Get the conversion rate
        rate_key = (from_currency, to_currency)
        if rate_key in cls.STATIC_RATES:
            rate = cls.STATIC_RATES[rate_key]
        else:
            # Fallback: calculate via EUR
            if from_currency in cls.RATES_TO_EUR and to_currency in cls.RATES_TO_EUR:
                # Convert to EUR first, then to target
                eur_amount = amount * cls.RATES_TO_EUR.get(from_currency, Decimal('1.00'))
                rate = Decimal('1.00') / cls.RATES_TO_EUR.get(to_currency, Decimal('1.00'))
                return (eur_amount * rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            else:
                # Unknown currency, return original amount
                return amount

        converted = amount * rate
        return converted.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    @classmethod
    def get_rate(cls, from_currency, to_currency):
        """
        Get the exchange rate between two currencies.

        Args:
            from_currency: Source currency code
            to_currency: Target currency code

        Returns:
            Decimal: Exchange rate
        """
        rate_key = (from_currency, to_currency)
        return cls.STATIC_RATES.get(rate_key, Decimal('1.00'))

    @classmethod
    def get_supported_currencies(cls):
        """Get list of supported currencies."""
        return list(cls.RATES_TO_EUR.keys())
