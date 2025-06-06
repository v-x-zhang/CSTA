# API Keys Security Setup

## 🔒 Environment Variables Setup

For security, API keys are now loaded from environment variables instead of being hardcoded in the source code.

### Quick Setup

1. **Copy the environment template:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` with your actual API keys:**
   ```bash
   # CS2 Trade-up Calculator Environment Variables
   PRICE_EMPIRE_API_KEY=your_actual_price_empire_key_here
   CSFLOAT_API_KEY=your_actual_csfloat_key_here
   ```

3. **Run the application:**
   ```bash
   python main.py --use-profitable-mock
   ```

### Getting API Keys

- **Price Empire API**: Get your key from [https://pricempire.com/api](https://pricempire.com/api)
- **CSFloat API**: Get your key from [https://csfloat.com/api](https://csfloat.com/api)

### Security Notes

- The `.env` file is automatically ignored by git (in `.gitignore`)
- Never commit API keys to version control
- The application will show a helpful error message if keys are missing
- Use `.env.example` as a template for new setups

### Troubleshooting

If you get an error about missing API keys:

1. Ensure `.env` file exists in the root directory
2. Check that your API keys are correctly formatted (no quotes, no spaces)
3. Verify that `python-dotenv` is installed: `pip install python-dotenv`
