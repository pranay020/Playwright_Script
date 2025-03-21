import json
import asyncio
from playwright.async_api import async_playwright

# Configuration details
USER_CREDENTIALS = {
    "username": "your_username",
    "password": "your_password"
}
URLS = {
    "login": "https://actual-website.com/login",
    "data_page": "https://actual-website.com/data"
}

SESSION_FILE = "session_data.json"

async def store_session(context):
    """Save browser session details to a file."""
    await context.storage_state(path=SESSION_FILE)
    print("Session details saved.")

async def retrieve_session(context):
    """Load session data if it exists."""
    try:
        await context.storage_state(path=SESSION_FILE)
        print("Session restored successfully.")
    except Exception as err:
        print(f"Session retrieval failed: {err}")

async def perform_login(page):
    """Log in to the application and retain session data."""
    await page.goto(URLS["login"])
    await page.fill("input[name='username']", USER_CREDENTIALS["username"])
    await page.fill("input[name='password']", USER_CREDENTIALS["password"])
    await page.click("button[type='submit']")
    await page.wait_for_selector("#dashboard", timeout=5000)
    print("Login successful.")

async def fetch_product_data(page):
    """Scrape product information from the data table, managing pagination."""
    extracted_data = []

    while True:
        table_rows = await page.locator("table tr").all()
        for row in table_rows[1:]:  # Ignore header row
            columns = await row.locator("td").all_text_contents()
            extracted_data.append({
                "product_name": columns[0],
                "price": columns[1],
                "availability": columns[2]
            })
        
        # Pagination handling
        next_btn = page.locator("button.next")
        if await next_btn.is_enabled():
            await next_btn.click()
            await page.wait_for_timeout(2000)  # Allow time for new data to load
        else:
            break

    return extracted_data



async def main():
    async with async_playwright() as playwright:
        # browser = await playwright.chromium.launch(headless=True)
        browser = await playwright.chromium.launch(headless=False)

        context = await browser.new_context()
        
        try:
            await retrieve_session(context)
            page = await context.new_page()
            # await page.goto(URLS["data_page"])
            print(f"Navigating to: {URLS['data_page']}")
            # await page.goto(DATA_PAGE_URL)
            print(f"Trying to open URL: {URLS['data_page']}")
            try:
                await page.goto(URLS["data_page"])
            except Exception as e:
                print(f"Failed to navigate: {e}")

            if not await page.is_visible("#product-table"):
                await perform_login(page)
                await store_session(context)
                print(f"Re-navigating to: {URLS['data_page']}")
                try:
                    await page.goto(URLS["data_page"])
                except Exception as e:
                    print(f"Failed to navigate: {e}")

            # Data extraction process
            products = await fetch_product_data(page)

            # Save extracted data to JSON
            with open("products.json", "w") as file:
                json.dump(products, file, indent=4)

            print("Data extraction completed.")

        except Exception as error:
            print(f"Error encountered: {error}")
        finally:
            await browser.close()

# Execute script
asyncio.run(main())