"""
Financial Validation Helper
Phase 4 Fix #18: Integer overflow validation for financial calculations

This module provides validation for financial values to prevent
integer overflow and ensure data integrity.
"""

from decimal import Decimal, InvalidOperation
from typing import Union, Optional
from helpers.app_config import AppConfig


# Maximum values based on database schema Numeric(10,2)
# Max value: 99999999.99 (10 digits total, 2 after decimal)
MAX_PRICE = Decimal(AppConfig.get_max_price())
MIN_PRICE = Decimal("0.00")

# Maximum quantity to prevent overflow in calculations
MAX_QUANTITY = 999999

# Maximum discount percentage
MAX_DISCOUNT_PERCENT = Decimal("100.00")
MIN_DISCOUNT_PERCENT = Decimal("0.00")


class FinancialValidationError(ValueError):
    """Raised when financial validation fails."""
    pass


def validate_price(
    value: Union[int, float, str, Decimal],
    field_name: str = "price",
    allow_zero: bool = True
) -> Decimal:
    """
    Validate price value to prevent overflow.
    
    Phase 4 Fix #18: Ensures price fits in Numeric(10,2) column.
    
    Args:
        value: Price value to validate
        field_name: Name of field for error messages
        allow_zero: Whether to allow zero values
        
    Returns:
        Validated Decimal value
        
    Raises:
        FinancialValidationError: If validation fails
    """
    try:
        # Convert to Decimal for precise validation
        if isinstance(value, Decimal):
            price = value
        else:
            price = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as e:
        raise FinancialValidationError(
            f"{field_name} harus berupa angka valid: {e}"
        )
    
    # Check for NaN or Infinity
    if not price.is_finite():
        raise FinancialValidationError(
            f"{field_name} tidak boleh NaN atau Infinity"
        )
    
    # Check minimum value
    min_allowed = MIN_PRICE if allow_zero else Decimal("0.01")
    if price < min_allowed:
        raise FinancialValidationError(
            f"{field_name} tidak boleh kurang dari {min_allowed}"
        )
    
    # Check maximum value (prevent overflow)
    if price > MAX_PRICE:
        raise FinancialValidationError(
            f"{field_name} tidak boleh lebih dari {MAX_PRICE:,.2f}"
        )
    
    # Ensure only 2 decimal places
    if price.as_tuple().exponent < -2:
        raise FinancialValidationError(
            f"{field_name} maksimal 2 angka desimal"
        )
    
    return price.quantize(Decimal("0.01"))


def validate_quantity(
    value: Union[int, float, str],
    field_name: str = "quantity",
    allow_zero: bool = False
) -> int:
    """
    Validate quantity to prevent overflow in calculations.
    
    Phase 4 Fix #18: Ensures quantity * price won't overflow.
    
    Args:
        value: Quantity value to validate
        field_name: Name of field for error messages
        allow_zero: Whether to allow zero values
        
    Returns:
        Validated integer quantity
        
    Raises:
        FinancialValidationError: If validation fails
    """
    try:
        # Convert to int
        if isinstance(value, float):
            if not value.is_integer():
                raise FinancialValidationError(
                    f"{field_name} harus berupa bilangan bulat"
                )
            quantity = int(value)
        else:
            quantity = int(value)
    except (ValueError, TypeError) as e:
        raise FinancialValidationError(
            f"{field_name} harus berupa angka bulat: {e}"
        )
    
    # Check minimum value
    min_allowed = 0 if allow_zero else 1
    if quantity < min_allowed:
        raise FinancialValidationError(
            f"{field_name} tidak boleh kurang dari {min_allowed}"
        )
    
    # Check maximum value (prevent overflow)
    if quantity > MAX_QUANTITY:
        raise FinancialValidationError(
            f"{field_name} tidak boleh lebih dari {MAX_QUANTITY:,}"
        )
    
    return quantity


def validate_discount(
    value: Union[int, float, str, Decimal],
    field_name: str = "discount"
) -> Decimal:
    """
    Validate discount percentage.
    
    Args:
        value: Discount percentage (0-100)
        field_name: Name of field for error messages
        
    Returns:
        Validated Decimal discount percentage
        
    Raises:
        FinancialValidationError: If validation fails
    """
    try:
        discount = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as e:
        raise FinancialValidationError(
            f"{field_name} harus berupa angka valid: {e}"
        )
    
    if not discount.is_finite():
        raise FinancialValidationError(
            f"{field_name} tidak boleh NaN atau Infinity"
        )
    
    if discount < MIN_DISCOUNT_PERCENT:
        raise FinancialValidationError(
            f"{field_name} tidak boleh kurang dari {MIN_DISCOUNT_PERCENT}"
        )
    
    if discount > MAX_DISCOUNT_PERCENT:
        raise FinancialValidationError(
            f"{field_name} tidak boleh lebih dari {MAX_DISCOUNT_PERCENT}"
        )
    
    return discount.quantize(Decimal("0.01"))


def validate_total(
    price: Union[int, float, str, Decimal],
    quantity: Union[int, float, str],
    discount_percent: Union[int, float, str, Decimal] = 0,
    field_name: str = "total"
) -> Decimal:
    """
    Validate and calculate total with overflow check.
    
    Phase 4 Fix #18: Ensures price * quantity won't overflow Numeric(10,2).
    
    Args:
        price: Unit price
        quantity: Quantity
        discount_percent: Discount percentage (0-100)
        field_name: Name of field for error messages
        
    Returns:
        Validated total amount
        
    Raises:
        FinancialValidationError: If calculation would overflow
    """
    # Validate individual components
    validated_price = validate_price(price, "price")
    validated_quantity = validate_quantity(quantity, "quantity")
    validated_discount = validate_discount(discount_percent, "discount")
    
    # Calculate subtotal
    try:
        subtotal = validated_price * validated_quantity
    except (InvalidOperation, OverflowError) as e:
        raise FinancialValidationError(
            f"Perhitungan {field_name} overflow: {e}"
        )
    
    # Check subtotal doesn't overflow
    if subtotal > MAX_PRICE:
        raise FinancialValidationError(
            f"{field_name} (Rp {subtotal:,.2f}) melebihi batas maksimum Rp {MAX_PRICE:,.2f}"
        )
    
    # Apply discount
    if validated_discount > 0:
        discount_multiplier = (Decimal("100") - validated_discount) / Decimal("100")
        total = subtotal * discount_multiplier
    else:
        total = subtotal
    
    # Final overflow check
    if total > MAX_PRICE:
        raise FinancialValidationError(
            f"{field_name} setelah diskon (Rp {total:,.2f}) melebihi batas maksimum Rp {MAX_PRICE:,.2f}"
        )
    
    return total.quantize(Decimal("0.01"))


def safe_add(*values: Union[int, float, str, Decimal]) -> Decimal:
    """
    Safely add multiple financial values with overflow check.
    
    Phase 4 Fix #18: Prevents overflow in sum calculations.
    
    Args:
        *values: Values to add
        
    Returns:
        Sum of values
        
    Raises:
        FinancialValidationError: If sum would overflow
    """
    total = Decimal("0.00")
    
    for value in values:
        try:
            validated = validate_price(value, "value", allow_zero=True)
            total += validated
        except FinancialValidationError:
            raise
        except Exception as e:
            raise FinancialValidationError(f"Error adding values: {e}")
    
    if total > MAX_PRICE:
        raise FinancialValidationError(
            f"Total (Rp {total:,.2f}) melebihi batas maksimum Rp {MAX_PRICE:,.2f}"
        )
    
    return total.quantize(Decimal("0.01"))


def safe_multiply(
    value1: Union[int, float, str, Decimal],
    value2: Union[int, float, str, Decimal]
) -> Decimal:
    """
    Safely multiply two financial values with overflow check.
    
    Phase 4 Fix #18: Prevents overflow in multiplication.
    
    Args:
        value1: First value
        value2: Second value
        
    Returns:
        Product of values
        
    Raises:
        FinancialValidationError: If product would overflow
    """
    try:
        val1 = Decimal(str(value1))
        val2 = Decimal(str(value2))
        result = val1 * val2
    except (InvalidOperation, ValueError, TypeError, OverflowError) as e:
        raise FinancialValidationError(f"Error multiplying values: {e}")
    
    if not result.is_finite():
        raise FinancialValidationError("Hasil perkalian tidak valid (NaN atau Infinity)")
    
    if result > MAX_PRICE:
        raise FinancialValidationError(
            f"Hasil perkalian (Rp {result:,.2f}) melebihi batas maksimum Rp {MAX_PRICE:,.2f}"
        )
    
    return result.quantize(Decimal("0.01"))


def format_currency(value: Union[int, float, str, Decimal]) -> str:
    """
    Format value as Indonesian Rupiah currency.
    
    Args:
        value: Value to format
        
    Returns:
        Formatted currency string (e.g., "Rp 1.234.567,89")
    """
    try:
        decimal_value = Decimal(str(value))
        # Format with thousand separators and 2 decimal places
        formatted = f"{decimal_value:,.2f}"
        # Replace comma with temp, dot with comma, temp with dot (Indonesian format)
        formatted = formatted.replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")
        return f"Rp {formatted}"
    except Exception:
        return f"Rp {value}"


# Example usage and tests
if __name__ == "__main__":
    print("Financial Validator Tests")
    print("=" * 50)
    
    # Test valid price
    try:
        price = validate_price(50000.50)
        print(f"✓ Valid price: {format_currency(price)}")
    except FinancialValidationError as e:
        print(f"✗ Price validation failed: {e}")
    
    # Test overflow price
    try:
        price = validate_price(100000000)
        print(f"✗ Should have failed: {price}")
    except FinancialValidationError as e:
        print(f"✓ Overflow detected: {e}")
    
    # Test valid total calculation
    try:
        total = validate_total(price=50000, quantity=10, discount_percent=10)
        print(f"✓ Valid total: {format_currency(total)}")
    except FinancialValidationError as e:
        print(f"✗ Total validation failed: {e}")
    
    # Test overflow total
    try:
        total = validate_total(price=99999999, quantity=2)
        print(f"✗ Should have failed: {total}")
    except FinancialValidationError as e:
        print(f"✓ Overflow detected: {e}")
    
    # Test safe add
    try:
        total = safe_add(10000, 20000, 30000)
        print(f"✓ Safe add: {format_currency(total)}")
    except FinancialValidationError as e:
        print(f"✗ Safe add failed: {e}")
    
    print("=" * 50)
