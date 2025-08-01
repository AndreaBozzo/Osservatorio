#!/usr/bin/env python3
"""
API Key Generation CLI Tool for Osservatorio ISTAT Data Platform

Command-line utility for managing API keys:
- Generate new API keys with custom scopes
- List existing API keys
- Revoke API keys
- Show API key statistics
- Test authentication

Usage:
    python scripts/generate_api_key.py create --name "My App" --scopes read,write
    python scripts/generate_api_key.py list
    python scripts/generate_api_key.py revoke --id 123
    python scripts/generate_api_key.py test --key osv_abc123...
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from src.auth.jwt_manager import JWTManager
from src.auth.models import APIKey
from src.auth.sqlite_auth import SQLiteAuthManager
from src.database.sqlite.repository import get_unified_repository
from src.utils.logger import get_logger

# Add src to path for imports
# Issue #84: Removed unsafe sys.path manipulation
# Use proper package imports or run from project root


logger = get_logger(__name__)


class APIKeyManager:
    """CLI API Key Management Tool"""

    def __init__(self):
        """Initialize API key manager"""
        try:
            # Issue #84: Use UnifiedDataRepository instead of direct manager access
            self.repository = get_unified_repository()
            self.sqlite_manager = self.repository.metadata_manager

            # Initialize auth manager
            self.auth_manager = SQLiteAuthManager(self.sqlite_manager)

            # Initialize JWT manager
            self.jwt_manager = JWTManager(self.sqlite_manager)

            print("✅ API Key Manager initialized successfully")

        except Exception as e:
            print(f"❌ Failed to initialize API Key Manager: {e}")
            sys.exit(1)

    def create_api_key(
        self, name: str, scopes: List[str], expires_days: Optional[int] = None
    ) -> APIKey:
        """Create new API key

        Args:
            name: Human-readable name for the API key
            scopes: List of permission scopes
            expires_days: Days until expiration (None for no expiration)

        Returns:
            Generated APIKey object
        """
        try:
            # Validate scopes
            valid_scopes = SQLiteAuthManager.VALID_SCOPES
            invalid_scopes = set(scopes) - set(valid_scopes)

            if invalid_scopes:
                print(f"❌ Invalid scopes: {invalid_scopes}")
                print(f"Valid scopes: {', '.join(valid_scopes)}")
                return None

            # Generate API key
            api_key = self.auth_manager.generate_api_key(name, scopes, expires_days)

            print(f"✅ API Key created successfully!")
            print(f"📝 Name: {api_key.name}")
            print(f"🔑 API Key: {api_key.key}")
            print(f"🏷️  Scopes: {', '.join(api_key.scopes)}")
            print(f"📅 Created: {api_key.created_at}")

            if api_key.expires_at:
                print(f"⏰ Expires: {api_key.expires_at}")
            else:
                print("⏰ Expires: Never")

            print(
                "\n⚠️  IMPORTANT: Save this API key securely. It won't be shown again!"
            )

            return api_key

        except Exception as e:
            print(f"❌ Failed to create API key: {e}")
            return None

    def list_api_keys(self, include_revoked: bool = False):
        """List all API keys"""
        try:
            api_keys = self.auth_manager.list_api_keys(include_revoked)

            if not api_keys:
                print("📋 No API keys found")
                return

            print(f"📋 Found {len(api_keys)} API key(s):")
            print()

            # Table header
            print(
                f"{'ID':<4} {'Name':<20} {'Scopes':<30} {'Status':<8} {'Created':<12} {'Last Used':<12}"
            )
            print("-" * 90)

            for key in api_keys:
                status = "Active" if key.is_active else "Revoked"
                created = (
                    key.created_at.strftime("%Y-%m-%d") if key.created_at else "Unknown"
                )
                last_used = (
                    key.last_used.strftime("%Y-%m-%d") if key.last_used else "Never"
                )
                scopes = ", ".join(key.scopes[:3])  # Show first 3 scopes
                if len(key.scopes) > 3:
                    scopes += "..."

                print(
                    f"{key.id:<4} {key.name:<20} {scopes:<30} {status:<8} {created:<12} {last_used:<12}"
                )

        except Exception as e:
            print(f"❌ Failed to list API keys: {e}")

    def revoke_api_key(self, api_key_id: int, reason: str = "manual_revocation"):
        """Revoke an API key"""
        try:
            success = self.auth_manager.revoke_api_key(api_key_id, reason)

            if success:
                print(f"✅ API Key {api_key_id} successfully revoked")
                print(f"📝 Reason: {reason}")
            else:
                print(f"❌ Failed to revoke API Key {api_key_id}")
                print("   Key may not exist or already be revoked")

        except Exception as e:
            print(f"❌ Failed to revoke API key: {e}")

    def test_api_key(self, api_key: str):
        """Test API key authentication"""
        try:
            # Verify API key
            key_obj = self.auth_manager.verify_api_key(api_key)

            if not key_obj:
                print("❌ API Key authentication failed")
                print("   Key may be invalid, expired, or revoked")
                return

            print("✅ API Key authentication successful!")
            print(f"📝 Name: {key_obj.name}")
            print(f"🏷️  Scopes: {', '.join(key_obj.scopes)}")
            print(f"📊 Usage Count: {key_obj.usage_count}")
            print(f"⚡ Rate Limit: {key_obj.rate_limit} requests/hour")

            if key_obj.expires_at:
                days_left = (key_obj.expires_at - datetime.now()).days
                print(f"⏰ Expires in: {days_left} days")
            else:
                print("⏰ Expires: Never")

            # Test JWT token generation
            try:
                auth_token = self.jwt_manager.create_access_token(key_obj)
                print(
                    f"🔐 JWT Token generated successfully (expires in {auth_token.expires_in}s)"
                )

                # Verify the token
                claims = self.jwt_manager.verify_token(auth_token.access_token)
                if claims:
                    print("✅ JWT Token verification successful")
                else:
                    print("❌ JWT Token verification failed")

            except Exception as e:
                print(f"⚠️  JWT token test failed: {e}")

        except Exception as e:
            print(f"❌ API key test failed: {e}")

    def show_statistics(self):
        """Show API key statistics"""
        try:
            all_keys = self.auth_manager.list_api_keys(include_revoked=True)
            active_keys = [k for k in all_keys if k.is_active]
            revoked_keys = [k for k in all_keys if not k.is_active]

            # Count by scopes
            scope_counts = {}
            for key in active_keys:
                for scope in key.scopes:
                    scope_counts[scope] = scope_counts.get(scope, 0) + 1

            # Recent usage (last 7 days)
            recent_cutoff = datetime.now() - timedelta(days=7)
            recent_keys = [
                k for k in active_keys if k.last_used and k.last_used > recent_cutoff
            ]

            print("📊 API Key Statistics")
            print("=" * 40)
            print(f"Total API Keys: {len(all_keys)}")
            print(f"Active Keys: {len(active_keys)}")
            print(f"Revoked Keys: {len(revoked_keys)}")
            print(f"Recently Used (7 days): {len(recent_keys)}")
            print()

            print("🏷️  Scopes Distribution:")
            for scope, count in sorted(scope_counts.items()):
                print(f"  {scope}: {count} keys")
            print()

            if active_keys:
                total_usage = sum(k.usage_count for k in active_keys)
                avg_usage = total_usage / len(active_keys)
                print(f"📈 Usage Statistics:")
                print(f"  Total Requests: {total_usage:,}")
                print(f"  Average per Key: {avg_usage:.1f}")

                # Most used key
                most_used = max(active_keys, key=lambda k: k.usage_count)
                print(
                    f"  Most Used: {most_used.name} ({most_used.usage_count:,} requests)"
                )

        except Exception as e:
            print(f"❌ Failed to show statistics: {e}")

    def cleanup_expired(self):
        """Clean up expired tokens and data"""
        try:
            # Clean up JWT tokens
            jwt_cleaned = self.jwt_manager.cleanup_expired_tokens()
            print(f"🧹 Cleaned up {jwt_cleaned} expired JWT tokens")

            print("✅ Cleanup completed successfully")

        except Exception as e:
            print(f"❌ Cleanup failed: {e}")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Osservatorio ISTAT API Key Management Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create API key with read/write access
  python scripts/generate_api_key.py create --name "My App" --scopes read,write

  # Create admin API key that expires in 30 days
  python scripts/generate_api_key.py create --name "Admin Tool" --scopes admin --expires 30

  # List all active API keys
  python scripts/generate_api_key.py list

  # List all API keys including revoked ones
  python scripts/generate_api_key.py list --include-revoked

  # Revoke API key by ID
  python scripts/generate_api_key.py revoke --id 123 --reason "Security breach"

  # Test API key authentication
  python scripts/generate_api_key.py test --key "osv_your_api_key_here"

  # Show usage statistics
  python scripts/generate_api_key.py stats

  # Clean up expired tokens
  python scripts/generate_api_key.py cleanup
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Create command
    create_parser = subparsers.add_parser("create", help="Create new API key")
    create_parser.add_argument("--name", required=True, help="API key name")
    create_parser.add_argument(
        "--scopes",
        required=True,
        help="Comma-separated list of scopes (read,write,admin,analytics,powerbi,tableau)",
    )
    create_parser.add_argument(
        "--expires", type=int, help="Expiration in days (default: never expires)"
    )

    # List command
    list_parser = subparsers.add_parser("list", help="List API keys")
    list_parser.add_argument(
        "--include-revoked", action="store_true", help="Include revoked API keys"
    )

    # Revoke command
    revoke_parser = subparsers.add_parser("revoke", help="Revoke API key")
    revoke_parser.add_argument("--id", type=int, required=True, help="API key ID")
    revoke_parser.add_argument(
        "--reason", default="manual_revocation", help="Revocation reason"
    )

    # Test command
    test_parser = subparsers.add_parser("test", help="Test API key")
    test_parser.add_argument("--key", required=True, help="API key to test")

    # Stats command
    subparsers.add_parser("stats", help="Show API key statistics")

    # Cleanup command
    subparsers.add_parser("cleanup", help="Clean up expired tokens")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Initialize manager
    manager = APIKeyManager()

    # Execute command
    try:
        if args.command == "create":
            scopes = [s.strip() for s in args.scopes.split(",")]
            manager.create_api_key(args.name, scopes, args.expires)

        elif args.command == "list":
            manager.list_api_keys(args.include_revoked)

        elif args.command == "revoke":
            manager.revoke_api_key(args.id, args.reason)

        elif args.command == "test":
            manager.test_api_key(args.key)

        elif args.command == "stats":
            manager.show_statistics()

        elif args.command == "cleanup":
            manager.cleanup_expired()

        else:
            print(f"❌ Unknown command: {args.command}")
            parser.print_help()

    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
