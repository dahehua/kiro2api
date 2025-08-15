#!/usr/bin/env python3
import argparse
import sys
from .app import main as start_app

def main():
    parser = argparse.ArgumentParser(
        prog='ki2',
        description='Kiro2API - Claude Sonnet 4 OpenAI Compatible API'
    )
    
    parser.add_argument(
        '-u', '--up', 
        action='store_true',
        help='Start the API server'
    )
    
    parser.add_argument(
        '-s', '--settings',
        action='store_true', 
        help='Show current settings and configuration'
    )
    
    args = parser.parse_args()
    
    if args.up:
        print("Starting Kiro2API server...")
        start_app()
    elif args.settings:
        show_settings()
    else:
        parser.print_help()

def show_settings():
    """Display current configuration settings"""
    import os
    from pathlib import Path
    
    print("Kiro2API Configuration:")
    print("=" * 30)
    
    # Token file location
    token_path = Path.home() / ".aws/sso/cache/kiro-auth-token.json"
    print(f"Token file: {token_path}")
    print(f"Token exists: {token_path.exists()}")
    
    # Environment variables
    print(f"\nEnvironment Variables:")
    print(f"API_KEY: {os.getenv('API_KEY', 'ki2api-key-2024')}")
    print(f"KIRO_ACCESS_TOKEN: {'Set' if os.getenv('KIRO_ACCESS_TOKEN') else 'Not set'}")
    print(f"KIRO_REFRESH_TOKEN: {'Set' if os.getenv('KIRO_REFRESH_TOKEN') else 'Not set'}")
    
    # Server info
    print(f"\nServer Configuration:")
    print(f"Host: 0.0.0.0")
    print(f"Port: 8989")
    print(f"URL: http://localhost:8989")

if __name__ == '__main__':
    main()