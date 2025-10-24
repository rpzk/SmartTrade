# Security

## Security Measures

### Error Handling
The application implements secure error handling:
- **User-facing errors**: Generic error messages are returned to users (e.g., "Failed to retrieve price data")
- **Server-side logging**: Detailed error information is logged server-side using `app.logger.error()` for debugging
- This approach prevents information leakage while maintaining debuggability

### Debug Mode
- Debug mode is **disabled by default** in production
- To enable debug mode (for development only), set `FLASK_DEBUG=true` in your `.env` file
- **Warning**: Never enable debug mode in production as it exposes the Werkzeug debugger

### API Keys
- API keys are stored in `.env` file which is in `.gitignore`
- Never commit API keys to version control
- Use environment variables for sensitive configuration

### Demo Mode
- The application can run in demo mode without API keys
- Demo mode uses simulated data and does not execute real trades
- Perfect for testing without exposing credentials

## CodeQL Security Analysis

The codebase has been scanned with CodeQL. Some alerts regarding "stack trace exposure" are false positives:
- The scanner detects `str(e)` in logging statements
- These logs are server-side only and not exposed to users
- User responses contain only generic error messages
- This is the correct secure pattern for error handling

## Recommendations

1. **Production Deployment**:
   - Use a production WSGI server (gunicorn, uWSGI) instead of Flask's development server
   - Set `FLASK_DEBUG=false` or leave it unset
   - Use HTTPS for all connections
   - Implement rate limiting
   - Set up proper monitoring and logging

2. **API Key Management**:
   - Use API keys with minimal required permissions
   - Rotate API keys regularly
   - Consider using hardware security modules (HSM) for key storage in production

3. **Testing**:
   - Always test with small amounts first
   - Use demo mode for development and testing
   - Monitor logs for suspicious activity

## Reporting Security Issues

If you discover a security vulnerability, please email the maintainer directly rather than opening a public issue.
