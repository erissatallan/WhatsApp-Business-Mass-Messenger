# Excel File Structure Guide

## Required Columns

### 1. `phone` (REQUIRED)
- **Purpose**: WhatsApp phone number for the contact
- **Formats Supported**:
  - `+254712345678` (International format - preferred)
  - `0712345678` (Kenya local - will be converted to +254712345678)
  - `254712345678` (Country code without + - will be converted)
  - `+1234567890` (Any country's international format)

### 2. `name` (REQUIRED)
- **Purpose**: Full name of the contact
- **Example**: "John Smith", "Grace Wanjiku", "Sarah Johnson"

## Optional Columns (For Message Personalization)

### Common Personalization Fields:
- `first_name` - First name only ("John", "Grace", "Sarah")
- `last_name` - Last name only ("Smith", "Wanjiku", "Johnson")
- `company` - Company/Business name ("Tech Solutions Ltd", "Fashion Inc")
- `city` - Location ("Nairobi", "Mombasa", "New York")
- `email` - Email address
- `last_purchase` - Previous purchase ("Silk Blouse", "Evening Dress")
- `purchase_amount` - Amount spent ("5000", "8500")

### Custom Fields:
You can add ANY additional columns and use them in your message templates!
Examples:
- `membership_level` - "VIP", "Premium", "Standard"
- `birthday` - "March 15", "2024-03-15"
- `favorite_color` - "Blue", "Red", "Black"
- `size_preference` - "Medium", "Large", "Small"

## Example Excel Structure

| phone | name | first_name | company | city | last_purchase | purchase_amount |
|-------|------|------------|---------|------|---------------|-----------------|
| +254712345678 | Jane Doe | Jane | Tech Solutions | Nairobi | Silk Blouse | 5000 |
| 0722123456 | John Smith | John | Retail Plus | Mombasa | Evening Dress | 8500 |
| +1234567890 | Sarah Johnson | Sarah | Fashion Inc | New York | Designer Bag | 12000 |

## Using in Message Templates

You can use any column in your message template with curly braces:

```
Hi {first_name}!

Thank you for being a valued customer at Mwihaki Intimates.

We noticed you purchased a {last_purchase} for KES {purchase_amount} from our {city} store.

We have exciting new arrivals that we think you'll love!

Best regards,
The Mwihaki Team
```

This becomes:
```
Hi Jane!

Thank you for being a valued customer at Mwihaki Intimates.

We noticed you purchased a Silk Blouse for KES 5000 from our Nairobi store.

We have exciting new arrivals that we think you'll love!

Best regards,
The Mwihaki Team
```

## File Requirements

- **Format**: .xlsx or .xls (Excel format)
- **Size**: Maximum 10MB
- **Encoding**: UTF-8 recommended for international characters
- **First Row**: Must contain column headers
- **Data**: Start from row 2 onwards

## Tips

1. **Phone Number Testing**: Start with small batches (5-10 contacts) to test
2. **Data Validation**: Clean your data - remove empty rows, validate phone formats
3. **Personalization**: More personal fields = more engaging messages
4. **Backup**: Keep a backup of your original file before uploading
