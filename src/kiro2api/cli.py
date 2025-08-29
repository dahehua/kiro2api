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
        '-s', '--start', 
        action='store_true',
        # dest='start',  # 将该选项的值存储在 args.up 中
        default=False,  # 默认值为 False
         # 如果没有提供该选项，则 args.up 将为 False
        help='Start the API server'
    )
    
    parser.add_argument(
        '-p', '--port', 
        required=False,                 # 这个选项是可选的
        type=int,                       # 期望接收一个整数类型的值
        dest="listen_port",            # 指定存储该值的属性名为 args.program_kind
        default=8989,               # 如果没有提供该选项，则使用默认值 8989
        help='Port to run the API server on (default: 8989)'
    )
    
    parser.add_argument(
        '-i', '--info',
        action='store_true', 
        dest='settings',  # 将该选项的值存储在 args.settings 中
        help='Show current settings and configuration'
    )
    
    parser.add_argument(
        '-v', '--version',
        action='store_true', 
        dest='_VERSION',  # 将该选项的值存储在 args._VERSION 中
        help='Show current version '
    )
    
    args = parser.parse_args()
    
    if args.start:
        port = args.listen_port
        print(f"Starting Kiro2API server on port {port}...")
        start_app(port)
    elif args.settings:
        show_settings()
    elif args._VERSION:
        show_version()
    else:
        parser.print_help()

def  show_version():
    """Display current version"""
    from . import __version__
    print(f"Kiro2API Version: {__version__}")

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
    # print(f"API_KEY: {os.getenv('API_KEY', 'ki2api-key-2024')}")
    print(f"KIRO_ACCESS_TOKEN: {'Set' if os.getenv('KIRO_ACCESS_TOKEN') else 'Not set'}")
    print(f"KIRO_REFRESH_TOKEN: {'Set' if os.getenv('KIRO_REFRESH_TOKEN') else 'Not set'}")
    
    # Server info
    print(f"\nServer Configuration:")
    print(f"Host: 0.0.0.0")
    print(f"Port: 8989")
    print(f"URL: http://localhost:8989")

if __name__ == '__main__':
    main()
    # python -m src.kiro2api.cli   