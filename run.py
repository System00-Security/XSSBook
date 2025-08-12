#!/usr/bin/env python3

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, init_db, populate_sample_data

if __name__ == '__main__':
    print("🚀 Starting XSSBook - Intentionally Vulnerable Social Network")
    print("=" * 60)
    
    # Initialize database and populate sample data
    print("📊 Initializing database...")
    init_db()
    
    print("👥 Populating sample data...")
    populate_sample_data()
    
    print("=" * 60)
    print("✅ XSSBook is ready!")
    print("🌐 Open your browser and navigate to: http://localhost:5000")
    print("👤 Demo accounts:")
    print("   Username: bret, antonette, samantha")
    print("   Password: password123")
    print("=" * 60)
    print("⚠️  WARNING: This application contains intentional vulnerabilities!")
    print("   Use only for educational purposes in isolated environments.")
    print("=" * 60)
    
    # Run the Flask app
    app.run(debug=True, host='0.0.0.0', port=5000)
