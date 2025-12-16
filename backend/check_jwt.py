"""
Test script to check available JWT exceptions
Run this to see what exceptions your PyJWT version has
"""
try:
    import jwt
    print(f"PyJWT version: {jwt.__version__}")

    # Check what's available in jwt.exceptions
    from jwt import exceptions
    print("\nAvailable exceptions in jwt.exceptions:")
    exc_list = [attr for attr in dir(exceptions) if not attr.startswith('_')]
    for exc in exc_list:
        print(f"  - {exc}")

    # Try different exception names
    print("\n✓ Testing which exceptions are available:")

    try:
        from jwt.exceptions import ExpiredSignatureError
        print("  ✓ ExpiredSignatureError - AVAILABLE")
    except ImportError:
        print("  ✗ ExpiredSignatureError - NOT AVAILABLE")

    try:
        from jwt.exceptions import InvalidTokenError
        print("  ✓ InvalidTokenError - AVAILABLE")
    except ImportError:
        print("  ✗ InvalidTokenError - NOT AVAILABLE")

    try:
        from jwt.exceptions import DecodeError
        print("  ✓ DecodeError - AVAILABLE")
    except ImportError:
        print("  ✗ DecodeError - NOT AVAILABLE")

    try:
        from jwt.exceptions import PyJWTError
        print("  ✓ PyJWTError - AVAILABLE")
    except ImportError:
        print("  ✗ PyJWTError - NOT AVAILABLE")

    try:
        from jwt import PyJWTError
        print("  ✓ PyJWTError (from jwt) - AVAILABLE")
    except ImportError:
        print("  ✗ PyJWTError (from jwt) - NOT AVAILABLE")

    try:
        from jwt import ExpiredSignatureError, InvalidTokenError
        print("  ✓ Import from jwt directly - AVAILABLE")
    except ImportError:
        print("  ✗ Import from jwt directly - NOT AVAILABLE")

except Exception as e:
    print(f"Error: {e}")
