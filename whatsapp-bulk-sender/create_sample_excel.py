import pandas as pd
import os

# Create sample data with various formats to demonstrate flexibility
sample_data = [
    {
        'phone': '+254712345678',
        'name': 'Jane Doe',
        'first_name': 'Jane',
        'last_name': 'Doe', 
        'company': 'Tech Solutions Ltd',
        'city': 'Nairobi',
        'last_purchase': 'Silk Blouse',
        'purchase_amount': '5000'
    },
    {
        'phone': '0722123456',  # Will be converted to +254722123456
        'name': 'John Smith',
        'first_name': 'John',
        'last_name': 'Smith',
        'company': 'Retail Plus',
        'city': 'Mombasa', 
        'last_purchase': 'Evening Dress',
        'purchase_amount': '8500'
    },
    {
        'phone': '+1234567890',  # International number
        'name': 'Sarah Johnson',
        'first_name': 'Sarah',
        'last_name': 'Johnson',
        'company': 'Fashion Forward Inc',
        'city': 'New York',
        'last_purchase': 'Designer Handbag',
        'purchase_amount': '12000'
    },
    {
        'phone': '254733567890',  # Full Kenya format without +
        'name': 'Michael Brown',
        'first_name': 'Michael', 
        'last_name': 'Brown',
        'company': 'Brown & Associates',
        'city': 'Kisumu',
        'last_purchase': 'Business Suit',
        'purchase_amount': '15000'
    },
    {
        'phone': '0799888777',
        'name': 'Grace Wanjiku',
        'first_name': 'Grace',
        'last_name': 'Wanjiku',
        'company': 'Wanjiku Enterprises',
        'city': 'Nakuru',
        'last_purchase': 'Traditional Wear',
        'purchase_amount': '6500'
    },
    {
        'phone': '+254701234567',
        'name': 'David Mwangi',
        'first_name': 'David',
        'last_name': 'Mwangi', 
        'company': 'Mwangi Holdings',
        'city': 'Eldoret',
        'last_purchase': 'Casual Wear Set',
        'purchase_amount': '4200'
    }
]

# Create DataFrame
df = pd.DataFrame(sample_data)

# Create sample Excel file
output_path = 'sample_contacts.xlsx'
df.to_excel(output_path, index=False, engine='openpyxl')

print(f"✅ Sample Excel file created: {output_path}")
print("\n📋 File Structure:")
print("Required columns:")
print("  - phone: Phone number (various formats supported)")
print("  - name: Full name of contact") 
print("\nOptional columns (for personalization):")
print("  - first_name, last_name: Individual name parts")
print("  - company: Company name")
print("  - city: Location")
print("  - last_purchase: Previous purchase")
print("  - purchase_amount: Amount spent")
print("  - Any other custom fields you want to use in messages")

print(f"\n📱 Phone Number Formats Supported:")
print("  - +254712345678 (International format)")
print("  - 0712345678 (Kenya local format - will be converted)")
print("  - 254712345678 (Country code without +)")
print("  - +1234567890 (Any international format)")

print(f"\n📄 Sample Data Preview:")
print(df.head(3).to_string(index=False))
