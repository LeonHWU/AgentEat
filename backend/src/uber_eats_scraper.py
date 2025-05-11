import asyncio
from langchain_openai import ChatOpenAI
from browser_use import Agent, Browser, BrowserConfig
from browser_use.browser.context import BrowserContextConfig

async def scrape_ubereats(postal_code, keywords):
    address = f"{postal_code}"
    task = f"""Go to https://deliveroo.co.uk/ and complete the following tasks:
    1. Enter the delivery address/postal code: {address}
    2. Search for {keywords} food
    3. From the search results, identify the top 10 restaurants
    4. For each restaurant:
    - Browse the entire restaurant page
    - Look for the {keywords} dish
    - If found, add it to the cart and proceed to checkout
    5 Return the results in a list of dictionaries with the following keys:
    - name: the name of the dish
    - price: the price of the dish
    - rating: the rating of the dish
    - restaurant: the name of the restaurant
    """

    browser = Browser(
        config=BrowserConfig(
            # Remove specific path to let Playwright manage the browser instance
            # chrome_instance_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            headless=True,
            new_context_config=BrowserContextConfig(
                disable_security=False,
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                minimum_wait_page_load_time=3,
                maximum_wait_page_load_time=30,
            )
        )
    )

    agent_1 = Agent(
        task=task,
        llm=ChatOpenAI(model='gpt-4.1-mini'),
        browser=browser,
    )

    try:
        results = await agent_1.run()
        print(results)
        return results
    finally:
        await browser.close() 