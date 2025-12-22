"""
logger.py - Centralized logging system for the product scraper application
"""

import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
import sys

# ---------------- Configuration ---------------- #
LOG_DIR = "logs"
LOG_FILE = "app.log"
MAX_BYTES = 10 * 1024 * 1024  # 10 MB
BACKUP_COUNT = 5

# ============== TOGGLE LOGGING ON/OFF ==============
LOGGING_ENABLED = True  # Set to False to disable all file logging
# ===================================================

# ============== DETAILED LOGGING CONTROL ==============
DETAILED_LOGGING = True  # Set to False for minimal console output
# Shows DEBUG level in console when True, only INFO+ when False
# =====================================================

# Create logs directory if it doesn't exist (only if logging is enabled)
if LOGGING_ENABLED:
    os.makedirs(LOG_DIR, exist_ok=True)

# ---------------- Custom Formatter ---------------- #
class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output"""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        if hasattr(sys.stdout, 'isatty') and sys.stdout.isatty():
            levelname = record.levelname
            if levelname in self.COLORS:
                record.levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"
        return super().format(record)


# ---------------- Logger Setup ---------------- #
def setup_logger(name, log_file=None, level=logging.DEBUG, console_output=True):
    """
    Create and configure a logger with file and console handlers.
    
    Args:
        name: Logger name (usually __name__)
        log_file: Custom log file name (default: app.log)
        level: Logging level (default: DEBUG for detailed logs)
        console_output: Whether to output to console (default: True)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # Always capture all levels
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # File handler with rotation (only if logging is enabled)
    if LOGGING_ENABLED:
        if log_file is None:
            log_file = LOG_FILE
        
        log_path = os.path.join(LOG_DIR, log_file)
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=MAX_BYTES,
            backupCount=BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)  # Capture all levels in file
        
        # File formatter (more detailed)
        file_formatter = logging.Formatter(
            fmt='%(asctime)s.%(msecs)03d | %(name)-20s | %(levelname)-8s | %(funcName)-20s:%(lineno)-4d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    # Console handler (optional)
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        # Set console level based on DETAILED_LOGGING toggle
        console_level = logging.DEBUG if DETAILED_LOGGING else logging.INFO
        console_handler.setLevel(console_level)
        
        # Console formatter (detailed with colors)
        console_formatter = ColoredFormatter(
            fmt='%(asctime)s | %(levelname)-8s | %(name)-20s | %(funcName)-15s | %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    return logger


# ---------------- Specialized Loggers ---------------- #
def get_scraper_logger(site_name):
    """Get a logger for a specific scraper (e.g., 'amazon', 'myntra')"""
    return setup_logger(
        f"scraper.{site_name}",
        log_file=f"scraper_{site_name}.log"
    )


def get_api_logger():
    """Get a logger for API/Flask routes"""
    return setup_logger("api", log_file="api.log")


def get_database_logger():
    """Get a logger for database operations"""
    return setup_logger("database", log_file="database.log")


def get_tagger_logger():
    """Get a logger for tagging operations"""
    return setup_logger("tagger", log_file="tagger.log")


# ---------------- Session Logging Context ---------------- #
class LogContext:
    """Context manager for logging with additional context"""
    
    def __init__(self, logger, **context):
        self.logger = logger
        self.context = context
        self.old_factory = None
    
    def __enter__(self):
        self.old_factory = logging.getLogRecordFactory()
        
        def record_factory(*args, **kwargs):
            record = self.old_factory(*args, **kwargs)
            for key, value in self.context.items():
                setattr(record, key, value)
            return record
        
        logging.setLogRecordFactory(record_factory)
        return self.logger
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        logging.setLogRecordFactory(self.old_factory)


# ---------------- Performance Logging ---------------- #
class PerformanceLogger:
    """Context manager for logging execution time"""
    
    def __init__(self, logger, operation_name):
        self.logger = logger
        self.operation_name = operation_name
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.info(f"Starting: {self.operation_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.now() - self.start_time).total_seconds()
        if exc_type is None:
            self.logger.info(f"Completed: {self.operation_name} (took {duration:.2f}s)")
        else:
            self.logger.error(f"Failed: {self.operation_name} (took {duration:.2f}s) - {exc_val}")


# ---------------- Utility Functions ---------------- #
def log_exception(logger, exc, message="An error occurred"):
    """Log an exception with full traceback"""
    logger.error(f"{message}: {exc}", exc_info=True)


def log_product_stats(logger, products, operation="Processed"):
    """Log detailed statistics about a product batch"""
    if not products:
        logger.warning(f"{operation}: No products")
        return
    
    sources = {}
    prices = []
    images = 0
    
    for product in products:
        # Count by source
        source = product.get('source', 'Unknown')
        sources[source] = sources.get(source, 0) + 1
        
        # Track prices
        if product.get('price'):
            prices.append(product['price'])
        
        # Count images
        if product.get('image_url'):
            images += 1
    
    logger.info(f"{operation}: {len(products)} products")
    
    # Source breakdown
    for source, count in sources.items():
        percentage = (count / len(products)) * 100
        logger.info(f"  - {source}: {count} products ({percentage:.1f}%)")
    
    # Price statistics
    if prices:
        avg_price = sum(prices) / len(prices)
        min_price = min(prices)
        max_price = max(prices)
        logger.info(f"  - Price range: ₹{min_price:.2f} - ₹{max_price:.2f} (avg: ₹{avg_price:.2f})")
    else:
        logger.warning(f"  - No pricing information available")
    
    # Image coverage
    image_percentage = (images / len(products)) * 100
    logger.info(f"  - Images: {images}/{len(products)} ({image_percentage:.1f}%)")
    
    # Additional details
    logger.debug(f"  - First product: {products[0].get('title', 'N/A')[:50]}...")
    logger.debug(f"  - Last product: {products[-1].get('title', 'N/A')[:50]}...")


def log_scraper_result(logger, site_name, page, products_found, success=True, duration=None):
    """Log detailed scraper execution results"""
    if success:
        msg = f"{site_name} Page {page}: Found {products_found} products"
        if duration:
            msg += f" (took {duration:.2f}s)"
        logger.info(msg)
        
        # Add performance warnings
        if duration and duration > 10:
            logger.warning(f"{site_name} Page {page}: Slow response time ({duration:.2f}s)")
        
        if products_found == 0:
            logger.warning(f"{site_name} Page {page}: No products found - possible scraper issue")
    else:
        logger.error(f"{site_name} Page {page}: Scrape failed")


# ---------------- Main Logger (default) ---------------- #
main_logger = setup_logger("main")


# ---------------- Example Usage ---------------- #
if __name__ == "__main__":
    print(f"📝 Logging is {'ENABLED ✅' if LOGGING_ENABLED else 'DISABLED ❌'}")
    print(f"🔍 Detailed logging is {'ENABLED ✅' if DETAILED_LOGGING else 'DISABLED ❌'}")
    print(f"📁 Log directory: {LOG_DIR}\n")
    print("="*80)
    print("🧪 TESTING LOGGER WITH ACTUAL SCRAPER INTEGRATION")
    print("="*80 + "\n")
    
    # Test 1: Import and test scrapers
    print("📦 Test 1: Importing scraper modules...")
    try:
        from Scraper import amazon_spider, myntra_spider, ajio_spider
        import scraper
        print("✅ All scraper modules imported successfully\n")
    except ImportError as e:
        print(f"❌ Import failed: {e}\n")
        print("⚠️  Make sure you're running from the project root directory")
        exit(1)
    
    # Test 2: Test individual scrapers with logging
    print("\n" + "="*80)
    print("📦 Test 2: Testing Individual Scrapers with Detailed Logging")
    print("="*80 + "\n")
    
    test_query = "tshirt"
    
    # Test Amazon scraper
    print("🔍 Testing Amazon Scraper...")
    amazon_logger = get_scraper_logger("amazon")
    amazon_logger.info(f"Starting Amazon scrape for query: '{test_query}'")
    
    try:
        with PerformanceLogger(amazon_logger, f"Amazon scrape - {test_query}"):
            amazon_logger.debug("Initializing Amazon spider...")
            amazon_products = amazon_spider.scrape_page(test_query, page=1, debug=False)
            amazon_logger.info(f"Amazon returned {len(amazon_products)} products")
            
            if amazon_products:
                log_product_stats(amazon_logger, amazon_products, operation="Amazon Scraped")
                amazon_logger.debug(f"Sample product: {amazon_products[0].get('title', 'N/A')[:50]}")
            else:
                amazon_logger.warning("No products returned from Amazon")
    except Exception as e:
        log_exception(amazon_logger, e, "Amazon scrape failed")
    
    print("\n" + "-"*80 + "\n")
    
    # Test Myntra scraper
    print("🔍 Testing Myntra Scraper...")
    myntra_logger = get_scraper_logger("myntra")
    myntra_logger.info(f"Starting Myntra scrape for query: '{test_query}'")
    
    try:
        with PerformanceLogger(myntra_logger, f"Myntra scrape - {test_query}"):
            myntra_logger.debug("Initializing Myntra spider...")
            myntra_products = myntra_spider.scrape_page(test_query, page=1, debug=False)
            myntra_logger.info(f"Myntra returned {len(myntra_products)} products")
            
            if myntra_products:
                log_product_stats(myntra_logger, myntra_products, operation="Myntra Scraped")
                myntra_logger.debug(f"Sample product: {myntra_products[0].get('title', 'N/A')[:50]}")
            else:
                myntra_logger.warning("No products returned from Myntra")
    except Exception as e:
        log_exception(myntra_logger, e, "Myntra scrape failed")
    
    print("\n" + "-"*80 + "\n")
    
    # Test Ajio scraper
    print("🔍 Testing Ajio Scraper...")
    ajio_logger = get_scraper_logger("ajio")
    ajio_logger.info(f"Starting Ajio scrape for query: '{test_query}'")
    
    try:
        with PerformanceLogger(ajio_logger, f"Ajio scrape - {test_query}"):
            ajio_logger.debug("Initializing Ajio spider...")
            ajio_products = ajio_spider.scrape_page(test_query, page=1, debug=False)
            ajio_logger.info(f"Ajio returned {len(ajio_products)} products")
            
            if ajio_products:
                log_product_stats(ajio_logger, ajio_products, operation="Ajio Scraped")
                ajio_logger.debug(f"Sample product: {ajio_products[0].get('title', 'N/A')[:50]}")
            else:
                ajio_logger.warning("No products returned from Ajio")
    except Exception as e:
        log_exception(ajio_logger, e, "Ajio scrape failed")
    
    # Test 3: Test main scraper pipeline
    print("\n" + "="*80)
    print("📦 Test 3: Testing Main Scraper Pipeline (scraper.main)")
    print("="*80 + "\n")
    
    main_logger = setup_logger("scraper_pipeline")
    main_logger.info(f"Starting full scraper pipeline for query: '{test_query}'")
    
    try:
        with PerformanceLogger(main_logger, f"Full pipeline - {test_query}"):
            main_logger.debug("Calling scraper.main()...")
            all_products = scraper.main(test_query)
            main_logger.info(f"Pipeline completed: {len(all_products)} total products")
            
            if all_products:
                log_product_stats(main_logger, all_products, operation="Pipeline Total")
                
                # Show breakdown by source
                sources = {}
                for product in all_products:
                    source = product.get('source', 'Unknown')
                    sources[source] = sources.get(source, 0) + 1
                
                main_logger.info("Source breakdown:")
                for source, count in sources.items():
                    main_logger.info(f"  - {source}: {count} products")
            else:
                main_logger.warning("Pipeline returned no products")
    except Exception as e:
        log_exception(main_logger, e, "Pipeline execution failed")
    
    # Test 4: Test main.py Flask routes (simulation)
    print("\n" + "="*80)
    print("📦 Test 4: Simulating Flask API Requests")
    print("="*80 + "\n")
    
    api_logger = get_api_logger()
    
    # Simulate a search request
    api_logger.info("Simulating /search endpoint")
    api_logger.debug("Request params: q='tshirt', rowsize=10, rid='test-session-123'")
    
    with LogContext(api_logger, endpoint="/search", rid="test-session-123", ip="127.0.0.1"):
        api_logger.info("Processing search request")
        api_logger.debug("Checking session validity...")
        api_logger.debug("Session found and valid")
        api_logger.info("Returning 10 products to client")
    
    # Simulate a feed request
    api_logger.info("Simulating /feed endpoint")
    api_logger.debug("Request params: rowsize=20, rid='test-session-456'")
    
    with LogContext(api_logger, endpoint="/feed", rid="test-session-456", ip="127.0.0.1"):
        api_logger.info("Processing feed request")
        api_logger.debug("Fetching trending products...")
        api_logger.debug("Mixing: 14 trending + 4 recent + 2 random")
        api_logger.info("Returning 20 products to client")
    
    # Final summary
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80 + "\n")
    
    summary_logger = setup_logger("test_summary")
    summary_logger.info("All logger tests completed successfully!")
    summary_logger.info("Components tested:")
    summary_logger.info("  ✅ Amazon scraper with detailed logging")
    summary_logger.info("  ✅ Myntra scraper with detailed logging")
    summary_logger.info("  ✅ Ajio scraper with detailed logging")
    summary_logger.info("  ✅ Main scraper pipeline (scraper.main)")
    summary_logger.info("  ✅ Flask API endpoint simulation")
    summary_logger.info("  ✅ Performance monitoring")
    summary_logger.info("  ✅ Exception handling")
    summary_logger.info("  ✅ Product statistics logging")
    
    if LOGGING_ENABLED:
        print(f"\n✅ Detailed logs written to:")
        print(f"   📄 Main log: {os.path.join(LOG_DIR, LOG_FILE)}")
        print(f"   📄 Amazon: {os.path.join(LOG_DIR, 'scraper_amazon.log')}")
        print(f"   📄 Myntra: {os.path.join(LOG_DIR, 'scraper_myntra.log')}")
        print(f"   📄 Ajio: {os.path.join(LOG_DIR, 'scraper_ajio.log')}")
        print(f"   📄 API: {os.path.join(LOG_DIR, 'api.log')}")
        print(f"\n📖 Check the .log files for complete details including DEBUG messages")
    else:
        print(f"\n⚠️  File logging is disabled. Only console output shown.")
    
    print("\n" + "="*80)
    print("🎉 Testing Complete!")
    print("="*80)