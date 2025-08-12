# XSSBook - Intentionally Vulnerable Social Network

XSSBook is a deliberately vulnerable social networking application built with Python Flask, designed for educational purposes to demonstrate various Cross-Site Scripting (XSS) vulnerabilities.

## Purpose

This application serves as a learning platform for:
- Understanding different types of XSS vulnerabilities
- Learning secure coding practices
- Practicing penetration testing techniques
- Educational demonstrations in cybersecurity courses

## Security Warning

**This application contains intentional security vulnerabilities and should NEVER be deployed to production or exposed to the internet. Use only in isolated, controlled environments for educational purposes.**

## Features

### Social Networking Features
- User registration and authentication
- User profiles with avatars, bio, and signatures
- Post creation with text, images, and videos
- Comment system
- Like functionality
- Friend requests and management
- Search functionality
- Personalization settings


## Installation

### Prerequisites
- Python 3.7 or higher
- pip (Python package installer)

### Setup
1. Clone or download the project files
2. Navigate to the project directory:
   ```bash
   cd XssBook
   ```

3. Install required packages:
   ```bash
   pip3 install -r requirements.txt
   ```

4. Run the application:
   ```bash
   python3 app.py
   ```

5. Open your browser and navigate to:
   ```
   http://localhost:5000
   ```

## Demo Accounts

The application automatically creates demo accounts with sample data:

- **Username:** bret, antonette, samantha, etc.
- **Password:** password123

These accounts come with pre-populated posts, comments, and profile information.
