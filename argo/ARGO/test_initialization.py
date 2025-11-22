#!/usr/bin/env python3
"""
Test script para verificar inicialización del sistema ARGO
"""
import os
import sys
from pathlib import Path

# Add ARGO to path
sys.path.insert(0, str(Path(__file__).parent))

def test_basic_initialization():
    """Test basic ARGO initialization"""
    print("=" * 70)
    print("ARGO System Initialization Test")
    print("=" * 70)

    try:
        # Test 1: Config
        print("\n[1/6] Testing Configuration...")
        from core.config import get_config
        config = get_config()
        print(f"✓ Config loaded: {config.version_display}")

        # Test 2: Logger
        print("\n[2/6] Testing Logger...")
        from core.logger import get_logger
        logger = get_logger("TestInit")
        logger.info("Logger test successful")
        print("✓ Logger working")

        # Test 3: Database
        print("\n[3/6] Testing Unified Database...")
        from core.unified_database import UnifiedDatabase
        db_path = Path(config.get("database.unified_db"))
        db_path.parent.mkdir(parents=True, exist_ok=True)
        db = UnifiedDatabase(db_path)
        print(f"✓ Database initialized: {db_path}")

        # Test 4: Model Router
        print("\n[4/6] Testing Model Router...")
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            print("⚠ WARNING: OPENAI_API_KEY not set in environment")
            print("  Model Router will not be functional without API key")
        else:
            print("✓ OpenAI API key detected")

        # Test 5: Plugin System
        print("\n[5/6] Testing Plugin System...")
        from core.plugins.manager import PluginManager
        plugin_manager = PluginManager(None)  # Simplified test
        print("✓ Plugin Manager initialized")

        # Test 6: Full Bootstrap
        print("\n[6/6] Testing Full Bootstrap...")
        from core.bootstrap import initialize_argo

        # Set minimal env
        os.environ.setdefault("PROJECT_NAME", "TEST_PROJECT")
        if not os.getenv("OPENAI_API_KEY"):
            print("⚠ Skipping full initialization (no OPENAI_API_KEY)")
            print("  Set OPENAI_API_KEY in .env to test full initialization")
        else:
            argo = initialize_argo("TEST_PROJECT")
            print(f"✓ ARGO fully initialized")
            print(f"  - Config: {argo['config'].version}")
            print(f"  - Database: {argo['unified_db']}")
            print(f"  - Project: {argo['project']['name']}")
            print(f"  - Plugins: {len(argo['plugins'].list_plugins())} loaded")

        print("\n" + "=" * 70)
        print("✓ INITIALIZATION TEST PASSED")
        print("=" * 70)
        return True

    except Exception as e:
        print("\n" + "=" * 70)
        print("✗ INITIALIZATION TEST FAILED")
        print("=" * 70)
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_basic_initialization()
    sys.exit(0 if success else 1)
