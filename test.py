#!/usr/bin/env python3
"""
Test script to identify and wipe km/hours data from PostgreSQL database.
This script is designed for the OTP Fuel Refund project.

IMPORTANT NOTES:
1. Currently the project uses SQLite, not PostgreSQL
2. No km/hours fields were found in the current models
3. This script provides both SQLite and PostgreSQL support
4. Always backup your database before running this script
"""

import os
import sys
import django
from django.conf import settings
from django.db import connection, transaction
from django.core.management import execute_from_command_line

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from main.models import CustomUser, UserDocument, UserSubmissionStatus, BusinessProfile, RootPassword


def check_database_type():
    """Check what type of database is being used."""
    db_engine = settings.DATABASES['default']['ENGINE']
    if 'sqlite' in db_engine:
        return 'sqlite'
    elif 'postgresql' in db_engine:
        return 'postgresql'
    else:
        return 'other'


def find_km_hours_fields():
    """
    Search for any fields that might contain km or hours data.
    This searches both Django models and raw database tables.
    """
    print("🔍 Searching for km/hours fields...")
    
    # Check Django models
    models_to_check = [CustomUser, UserDocument, UserSubmissionStatus, BusinessProfile, RootPassword]
    
    km_hours_fields = []
    
    for model in models_to_check:
        print(f"Checking model: {model.__name__}")
        for field in model._meta.fields:
            field_name = field.name.lower()
            if any(keyword in field_name for keyword in ['km', 'kilometer', 'hours', 'hour', 'distance', 'mileage']):
                km_hours_fields.append({
                    'model': model.__name__,
                    'field': field.name,
                    'type': 'Django Model Field'
                })
                print(f"  Found field: {field.name}")
    
    # Check raw database tables
    db_type = check_database_type()
    print(f"\nDatabase type: {db_type}")
    
    with connection.cursor() as cursor:
        if db_type == 'postgresql':
            # PostgreSQL query to find tables and columns
            cursor.execute("""
                SELECT table_name, column_name, data_type 
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND (LOWER(column_name) LIKE '%km%' 
                     OR LOWER(column_name) LIKE '%kilometer%' 
                     OR LOWER(column_name) LIKE '%hours%' 
                     OR LOWER(column_name) LIKE '%hour%'
                     OR LOWER(column_name) LIKE '%distance%'
                     OR LOWER(column_name) LIKE '%mileage%')
                ORDER BY table_name, column_name;
            """)
            
        elif db_type == 'sqlite':
            # SQLite query to find tables and columns
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%';
            """)
            tables = cursor.fetchall()
            
            for table in tables:
                table_name = table[0]
                cursor.execute(f"PRAGMA table_info({table_name});")
                columns = cursor.fetchall()
                
                for column in columns:
                    column_name = column[1].lower()
                    if any(keyword in column_name for keyword in ['km', 'kilometer', 'hours', 'hour', 'distance', 'mileage']):
                        km_hours_fields.append({
                            'model': table_name,
                            'field': column[1],
                            'type': 'Database Column'
                        })
                        print(f"  Found column: {table_name}.{column[1]}")
        else:
            print("Unsupported database type for detailed column search")
    
    return km_hours_fields


def wipe_km_hours_data(km_hours_fields, dry_run=True):
    """
    Wipe km/hours data from the database.
    
    Args:
        km_hours_fields: List of fields to wipe
        dry_run: If True, only show what would be done without actually doing it
    """
    if not km_hours_fields:
        print("✅ No km/hours fields found to wipe!")
        return
    
    print(f"\n{'🔍 DRY RUN - ' if dry_run else '⚠️  EXECUTING - '}Wiping km/hours data...")
    
    db_type = check_database_type()
    
    with connection.cursor() as cursor:
        for field_info in km_hours_fields:
            model_name = field_info['model']
            field_name = field_info['field']
            
            if field_info['type'] == 'Django Model Field':
                # Handle Django model fields
                try:
                    model_class = globals()[model_name]
                    
                    if dry_run:
                        count = model_class.objects.filter(**{f"{field_name}__isnull": False}).count()
                        print(f"  Would wipe {count} records from {model_name}.{field_name}")
                    else:
                        # Set field to None or empty string depending on field type
                        field_obj = model_class._meta.get_field(field_name)
                        if field_obj.null:
                            model_class.objects.update(**{field_name: None})
                        else:
                            model_class.objects.update(**{field_name: ''})
                        print(f"  ✅ Wiped {model_name}.{field_name}")
                        
                except Exception as e:
                    print(f"  ❌ Error wiping {model_name}.{field_name}: {e}")
            
            elif field_info['type'] == 'Database Column':
                # Handle raw database columns
                table_name = model_name
                
                if dry_run:
                    if db_type == 'postgresql':
                        cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {field_name} IS NOT NULL;")
                    else:  # sqlite
                        cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {field_name} IS NOT NULL;")
                    
                    count = cursor.fetchone()[0]
                    print(f"  Would wipe {count} records from {table_name}.{field_name}")
                else:
                    try:
                        if db_type == 'postgresql':
                            cursor.execute(f"UPDATE {table_name} SET {field_name} = NULL;")
                        else:  # sqlite
                            cursor.execute(f"UPDATE {table_name} SET {field_name} = NULL;")
                        print(f"  ✅ Wiped {table_name}.{field_name}")
                    except Exception as e:
                        print(f"  ❌ Error wiping {table_name}.{field_name}: {e}")


def backup_database():
    """Create a backup of the database before making changes."""
    print("💾 Creating database backup...")
    
    db_type = check_database_type()
    db_config = settings.DATABASES['default']
    
    if db_type == 'sqlite':
        import shutil
        db_path = db_config['NAME']
        backup_path = f"{db_path}.backup"
        shutil.copy2(db_path, backup_path)
        print(f"✅ SQLite backup created: {backup_path}")
        
    elif db_type == 'postgresql':
        import subprocess
        db_name = db_config['NAME']
        backup_file = f"{db_name}_backup.sql"
        
        # Create pg_dump command
        cmd = ['pg_dump', '-h', db_config.get('HOST', 'localhost'), 
               '-p', str(db_config.get('PORT', 5432)),
               '-U', db_config.get('USER', 'postgres'),
               '-d', db_name, '-f', backup_file]
        
        try:
            subprocess.run(cmd, check=True)
            print(f"✅ PostgreSQL backup created: {backup_file}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to create PostgreSQL backup: {e}")
            print("Please create a manual backup before proceeding!")
            return False
    else:
        print("⚠️  Unsupported database type for automatic backup")
        print("Please create a manual backup before proceeding!")
        return False
    
    return True


def main():
    """Main function to run the km/hours data wiping process."""
    print("🚀 OTP Fuel Refund - KM/Hours Data Wiping Script")
    print("=" * 50)
    
    # Check database type
    db_type = check_database_type()
    print(f"Database: {db_type}")
    
    # Find km/hours fields
    km_hours_fields = find_km_hours_fields()
    
    if not km_hours_fields:
        print("\n✅ No km/hours fields found in the database!")
        print("The current models don't contain any fields with km or hours data.")
        return
    
    print(f"\n📋 Found {len(km_hours_fields)} km/hours fields:")
    for field in km_hours_fields:
        print(f"  - {field['model']}.{field['field']} ({field['type']})")
    
    # Ask for confirmation
    print("\n⚠️  WARNING: This will permanently delete km/hours data!")
    response = input("Do you want to proceed? (yes/no): ").lower().strip()
    
    if response not in ['yes', 'y']:
        print("❌ Operation cancelled.")
        return
    
    # Create backup
    if not backup_database():
        print("❌ Cannot proceed without backup. Exiting.")
        return
    
    # Dry run first
    print("\n🔍 Running dry run...")
    wipe_km_hours_data(km_hours_fields, dry_run=True)
    
    # Final confirmation
    print("\n⚠️  FINAL WARNING: This will permanently delete the data!")
    final_response = input("Type 'DELETE' to confirm: ").strip()
    
    if final_response != 'DELETE':
        print("❌ Operation cancelled.")
        return
    
    # Execute the wipe
    print("\n🗑️  Executing data wipe...")
    with transaction.atomic():
        wipe_km_hours_data(km_hours_fields, dry_run=False)
    
    print("\n✅ Data wiping completed!")
    print("💡 Remember to test your application to ensure everything works correctly.")


def setup_postgresql():
    """
    Helper function to setup PostgreSQL configuration.
    This is for reference - you'll need to update settings.py manually.
    """
    postgresql_config = """
# Add this to your settings.py to use PostgreSQL:

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'your_database_name',
        'USER': 'your_username',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Don't forget to install psycopg2:
# pip install psycopg2-binary

# And run migrations:
# python manage.py migrate
"""
    print("PostgreSQL Configuration Template:")
    print(postgresql_config)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--setup-postgresql':
        setup_postgresql()
    else:
        main()





