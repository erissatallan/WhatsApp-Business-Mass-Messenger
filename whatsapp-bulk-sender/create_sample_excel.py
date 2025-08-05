import pandas as pd
import os

# Create sample data with your specific contacts
sample_data = [
    {
        'phone': '0759469851',
        'name': 'Allan Erissat',
        'first_name': 'Allan',
        'last_name': 'Erissat',
        'company': 'N/A',
        'city': 'Nairobi',
        'last_purchase': 'Socks',
        'purchase_amount': '1000'
    },
    {
        'phone': '0716369120',
        'name': 'Mwihaki Last_Name',
        'first_name': 'Mwihaki',
        'last_name': 'Last_Name',
        'company': 'M.I.',
        'city': 'Nairobi',
        'last_purchase': 'Socks',
        'purchase_amount': '1200'
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
