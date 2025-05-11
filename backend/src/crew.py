from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
import os
import sys
from pathlib import Path
from crewai.tools import tool
import asyncio
import threading
from .uber_eats_scraper import scrape_ubereats
import json
from datetime import datetime, timedelta
import random

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent.parent))


# @tool("FoodSearch")
# def food_search(postal_code: str, keywords: str) -> list:
#     """Search for food given a postal code and keywords, returning real deliveroo results.
#     """
#     results = []
#     error = None
#
#     def run_in_thread():
#         nonlocal results, error
#         try:
#             # Create and manage a new event loop for this thread
#             loop = asyncio.new_event_loop()
#             asyncio.set_event_loop(loop)
#             results = loop.run_until_complete(scrape_ubereats(postal_code, keywords))
#             loop.close()
#         except Exception as e:
#             print(f"Error in scraper thread: {e}")
#             error = e
#
#     # Create and start the thread
#     thread = threading.Thread(target=run_in_thread)
#     thread.start()
#     thread.join() # Wait for the thread to complete
#
#     if error:
#         # Return an error indication if the thread failed
#         return [{ "error": f"Failed to get results due to an error in the scraper: {error}" }]
#     else:
#         return results

@tool("FoodSearch")
def food_search(postal_code: str, keywords: str, show_alternatives: bool = False) -> list:
    """
    Search for food given a postal code and keywords. Returns a result based on the keywords provided.
    
    Supported keywords and their results:
    - "pizza": Returns a Margherita Pizza from Pizza Place.
    - "sushi": Returns a Salmon Sushi Set from Sushi Bar.
    - "burger": Returns a Classic Burger from Burger Joint.
    - "chinese": Returns Chinese restaurant options.
    
    If the keywords do not match any of the above, an error message is returned.
    """
    # This dictionary will be injected into the agent below
    keyword_map = {
        "pizza": [{"name": "Margherita Pizza", "price": 10.99, "restaurant": "Pizza Place", "rating": 4.5}],
        "sushi": [{"name": "Salmon Sushi Set", "price": 15.99, "restaurant": "Sushi Bar", "rating": 4.7}],
        "burger": [{"name": "Classic Burger", "price": 9.99, "restaurant": "Burger Joint", "rating": 4.3}],
        "chinese": [
            {"name": "Ni HAO", "specialty": "Kung Pao Chicken", "rating": 4.7, "reviews": 500, "platform": "UberEats"},
            {"name": "Wok & Roll", "specialty": "Crispy duck pancakes", "rating": 4.5, "reviews": 300, "platform": "Deliveroo"},
            {"name": "Bamboo House", "specialty": "Beef in black bean sauce", "rating": 4.6, "reviews": 450, "platform": "Just Eat"}
        ]
    }
    
    # Alternative recommendations for when initial options are rejected
    alternative_keyword_map = {
        "pizza": [{"name": "Pepperoni Pizza", "price": 12.99, "restaurant": "Pizza Express", "rating": 4.6}],
        "sushi": [{"name": "Dragon Roll", "price": 16.99, "restaurant": "Sushi Master", "rating": 4.8}],
        "burger": [{"name": "Double Cheeseburger", "price": 11.99, "restaurant": "Burger King", "rating": 4.4}],
        "chinese": [
            {"name": "Xin Kai", "specialty": "Kung Pao Chicken", "description": "Spicy chicken with peanuts and vegetables in a savory sauce", "rating": 4.7, "reviews": 500, "platform": "UberEats"},
            {"name": "Imperial Palace", "specialty": "Chicken with Garlic Sauce", "description": "Tender chicken with garlic and ginger sauce", "rating": 4.8, "reviews": 320, "platform": "Deliveroo"},
            {"name": "Dragon Phoenix", "specialty": "Gong Bao Ji Ding", "description": "Traditional Kung Pao Chicken", "rating": 4.9, "reviews": 400, "platform": "Just Eat"}
        ]
    }
    
    for key, value in keyword_map.items():
        if key in keywords.lower():
            if show_alternatives:
                # If alternatives are requested, check if there are alternatives for this keyword
                if key in alternative_keyword_map:
                    return alternative_keyword_map[key]
                else:
                    # If no alternatives exist, return the original results
                    return value
            else:
                return value
    return [{"error": "No matching food found for the given keywords."}]


@tool("SaveUserPreferences")
def save_user_preferences(postal_code: str, delivery_time: str = None) -> dict:
    """Save user preferences like postal code and delivery time."""
    if not postal_code:
        return {"error": "Missing postal code"}
    
    # In a real implementation, this would save to a database
    # For this simulation, we'll just return a success message
    return {
        "postal_code": postal_code,
        "delivery_time": delivery_time,
        "message": f"Saved preferences: Postal code {postal_code}" + 
                  (f", Delivery time {delivery_time}" if delivery_time else "")
    }


@tool("SearchRestaurants")
def search_restaurants(postal_code: str, cuisine: str, delivery_time: str = None, show_alternatives: bool = False) -> list:
    """Search for restaurants by cuisine type that deliver to the given postal code."""
    if not postal_code or not cuisine:
        return [{"error": "Missing postal code or cuisine type"}]
    
    # In a real implementation, this would query a database or API
    # For this simulation, we'll return mock data
    restaurants = {
        "chinese": [
            {"name": "Xin Kai", "specialty": "Kung Pao Chicken", "rating": 4.7, "reviews": 500, "platform": "UberEats"},
            {"name": "Wok & Roll", "specialty": "Crispy duck pancakes", "rating": 4.5, "reviews": 300, "platform": "Deliveroo"},
            {"name": "Bamboo House", "specialty": "Beef in black bean sauce", "rating": 4.6, "reviews": 450, "platform": "Just Eat"}
        ],
        "italian": [
            {"name": "Pasta Paradise", "specialty": "Homemade pasta", "rating": 4.8, "reviews": 420, "platform": "UberEats"},
            {"name": "Pizza Express", "specialty": "Wood-fired pizza", "rating": 4.6, "reviews": 380, "platform": "Deliveroo"},
            {"name": "Roma Italian", "specialty": "Authentic Italian cuisine", "rating": 4.7, "reviews": 350, "platform": "Just Eat"}
        ],
        "indian": [
            {"name": "Spice Garden", "specialty": "Butter chicken", "rating": 4.8, "reviews": 450, "platform": "UberEats"},
            {"name": "Taj Mahal", "specialty": "Biryani", "rating": 4.7, "reviews": 380, "platform": "Deliveroo"},
            {"name": "Royal Indian", "specialty": "Curry", "rating": 4.6, "reviews": 320, "platform": "Just Eat"}
        ]
    }
    
    # Alternative recommendations for when initial options are rejected
    alternative_restaurants = {
        "chinese": [
            {"name": "Xin Kai", "specialty": "Kung Pao Chicken", "description": "Spicy chicken with peanuts and vegetables in a savory sauce", "rating": 4.7, "reviews": 500, "platform": "UberEats"},
            {"name": "Imperial Palace", "specialty": "Chicken with Garlic Sauce", "description": "Tender chicken with garlic and ginger sauce", "rating": 4.8, "reviews": 320, "platform": "Deliveroo"},
            {"name": "Dragon Phoenix", "specialty": "Gong Bao Ji Ding", "description": "Traditional Kung Pao Chicken", "rating": 4.9, "reviews": 400, "platform": "Just Eat"}
        ],
        "italian": [
            {"name": "La Cucina", "specialty": "Homemade lasagna", "description": "Layers of pasta with rich meat sauce and cheese", "rating": 4.9, "reviews": 380, "platform": "UberEats"},
            {"name": "Pasta Express", "specialty": "Seafood linguine", "description": "Fresh seafood with linguine in white wine sauce", "rating": 4.7, "reviews": 320, "platform": "Deliveroo"},
            {"name": "Roma Bella", "specialty": "Margherita pizza", "description": "Classic pizza with tomato, mozzarella, and basil", "rating": 4.8, "reviews": 350, "platform": "Just Eat"}
        ],
        "indian": [
            {"name": "Spice Garden", "specialty": "Butter chicken", "description": "Tender chicken in rich, creamy tomato sauce", "rating": 4.8, "reviews": 450, "platform": "UberEats"},
            {"name": "Taj Mahal", "specialty": "Biryani", "description": "Fragrant rice dish with spices and tender meat", "rating": 4.7, "reviews": 380, "platform": "Deliveroo"},
            {"name": "Royal Indian", "specialty": "Curry", "description": "Rich, flavorful curry with your choice of protein", "rating": 4.6, "reviews": 320, "platform": "Just Eat"}
        ]
    }
    
    if cuisine.lower() in restaurants:
        if show_alternatives:
            return alternative_restaurants[cuisine.lower()]
        else:
            return restaurants[cuisine.lower()]
    else:
        return [{"error": f"No restaurants found for cuisine: {cuisine}"}]


@tool("GetRestaurantMenu")
def get_restaurant_menu(restaurant_name: str) -> dict:
    """Get the menu for a specific restaurant."""
    if not restaurant_name:
        return {"error": "Missing restaurant name"}
    
    # In a real implementation, this would query a database or API
    # For this simulation, we'll return mock data
    menus = {
        "Dragon Phoenix": {
            "name": "Dragon Phoenix",
            "menu": [
                {"name": "Gong Bao Ji Ding", "description": "Tender chicken pieces stir-fried with peanuts, vegetables, and chili in a savory sauce", "price": 13.99},
                {"name": "Egg Fried Rice", "description": "Fluffy rice with scrambled egg and spring onions", "price": 3.50},
                {"name": "Beef in Black Bean Sauce", "description": "Sliced beef with black bean sauce and vegetables", "price": 14.99},
                {"name": "Sweet and Sour Chicken", "description": "Crispy chicken in sweet and sour sauce with pineapple", "price": 12.99},
                {"name": "Spring Rolls", "description": "Crispy vegetable spring rolls with sweet chili sauce", "price": 4.99},
                {"name": "Still Water (500ml)", "description": "Bottled still water", "price": 1.50},
                {"name": "Coca Cola (330ml)", "description": "Bottled Coca Cola", "price": 1.99}
            ]
        },
        "Golden Dragon": {
            "name": "Golden Dragon",
            "menu": [
                {"name": "Sweet and Sour Chicken", "description": "Crispy chicken in sweet and sour sauce with pineapple", "price": 12.99},
                {"name": "Egg Fried Rice", "description": "Fluffy rice with scrambled egg and spring onions", "price": 3.50},
                {"name": "Beef in Black Bean Sauce", "description": "Sliced beef with black bean sauce and vegetables", "price": 14.99},
                {"name": "Kung Pao Chicken", "description": "Spicy chicken with peanuts and vegetables", "price": 13.99},
                {"name": "Spring Rolls", "description": "Crispy vegetable spring rolls with sweet chili sauce", "price": 4.99},
                {"name": "Still Water (500ml)", "description": "Bottled still water", "price": 1.50},
                {"name": "Coca Cola (330ml)", "description": "Bottled Coca Cola", "price": 1.99}
            ]
        },
        "Xin Kai": {
            "name": "Xin Kai",
            "menu": [
                {"name": "Sweet and Sour Chicken", "description": "Crispy chicken in sweet and sour sauce with pineapple", "price": 12.99},
                {"name": "Egg Fried Rice", "description": "Fluffy rice with scrambled egg and spring onions", "price": 3.50},
                {"name": "Beef in Black Bean Sauce", "description": "Sliced beef with black bean sauce and vegetables", "price": 14.99},
                {"name": "Kung Pao Chicken", "description": "Spicy chicken with peanuts and vegetables", "price": 17.83},
                {"name": "Spring Rolls", "description": "Crispy vegetable spring rolls with sweet chili sauce", "price": 4.99},
                {"name": "Still Water (500ml)", "description": "Bottled still water", "price": 1.50},
                {"name": "Coca Cola (330ml)", "description": "Bottled Coca Cola", "price": 1.99}
            ]
        }
    }
    
    if restaurant_name in menus:
        return menus[restaurant_name]
    else:
        return {"error": f"Menu not found for restaurant: {restaurant_name}"}


@tool("AddToCart")
def add_to_cart(restaurant_name: str, items: list) -> dict:
    """Add items to the cart for a specific restaurant."""
    if not restaurant_name or not items:
        return {"error": "Missing restaurant name or items"}
    
    # In a real implementation, this would manage a shopping cart in a database
    # For this simulation, we'll just return a success message with the cart contents
    return {
        "restaurant": restaurant_name,
        "items": items,
        "message": f"Added {len(items)} items to cart from {restaurant_name}"
    }


@tool("CalculateTotal")
def calculate_total(cart_items: list) -> dict:
    """Calculate the total price for the items in the cart."""
    if not cart_items:
        return {"error": "Cart is empty"}
    
    # In a real implementation, this would calculate based on actual prices
    # For this simulation, we'll use a simplified calculation
    subtotal = sum(item.get("price", 0) for item in cart_items)
    delivery_fee = 2.99
    
    # Apply discount if subtotal is over £18
    discount = 0
    if subtotal >= 18:
        discount = subtotal * 0.15  # 15% discount
    
    # Reduce delivery fee if discount is applied
    if discount > 0:
        delivery_fee = 1.69
    
    total = subtotal - discount + delivery_fee
    
    return {
        "subtotal": round(subtotal, 2),
        "discount": round(discount, 2),
        "delivery_fee": round(delivery_fee, 2),
        "total": round(total, 2),
        "message": f"Subtotal: £{round(subtotal, 2)}, Discount: £{round(discount, 2)}, Delivery fee: £{round(delivery_fee, 2)}, Total: £{round(total, 2)}"
    }


@tool("ProcessOrder")
def process_order(postal_code: str, delivery_time: str, payment_method: str, cart_items: list) -> dict:
    """Process the order with the given details."""
    if not postal_code or not payment_method or not cart_items:
        return {"error": "Missing required order details"}
    
    # In a real implementation, this would process the order through a payment gateway
    # For this simulation, we'll just return a success message
    order_id = f"ORD-{random.randint(10000, 99999)}"
    
    return {
        "order_id": order_id,
        "postal_code": postal_code,
        "delivery_time": delivery_time,
        "payment_method": payment_method,
        "items": cart_items,
        "status": "confirmed",
        "message": f"Order {order_id} has been confirmed for delivery to {postal_code} at {delivery_time}. Payment method: {payment_method}."
    }


@tool("PayOrder")
def pay_order(order_id: str, payment_method: str) -> dict:
    """Pay for an order given an order ID and payment method."""
    if not order_id or not payment_method:
        return {"error": "Missing order_id or payment_method"}
    return {
        "order_id": order_id,
        "status": "paid",
        "payment_method": payment_method,
        "message": f"Order {order_id} has been paid using {payment_method}."
    }


@tool("GenerateOrderSummary")
def generate_order_summary(restaurant_name: str, items: list, postal_code: str, delivery_time: str = None) -> dict:
    """Generate a comprehensive summary of the order before placing it."""
    if not restaurant_name or not items or not postal_code:
        return {"error": "Missing required order details"}
    
    # Calculate the total price
    subtotal = sum(item.get("price", 0) for item in items)
    delivery_fee = 2.99
    
    # Apply discount if subtotal is over £18
    discount = 0
    if subtotal >= 18:
        discount = subtotal * 0.15  # 15% discount
    
    # Reduce delivery fee if discount is applied
    if discount > 0:
        delivery_fee = 1.69
    
    total = subtotal - discount + delivery_fee
    
    # Generate a random ETA (in a real implementation, this would be calculated based on restaurant preparation time and distance)
    eta_minutes = random.randint(30, 45)
    
    # Format the delivery time
    if delivery_time:
        formatted_delivery_time = delivery_time
    else:
        # If no specific delivery time is provided, use current time + ETA
        current_time = datetime.now()
        eta_time = current_time + timedelta(minutes=eta_minutes)
        formatted_delivery_time = eta_time.strftime("%I:%M %p")
    
    # Create a formatted summary
    summary = {
        "restaurant": restaurant_name,
        "items": items,
        "postal_code": postal_code,
        "delivery_time": formatted_delivery_time,
        "subtotal": round(subtotal, 2),
        "discount": round(discount, 2),
        "delivery_fee": round(delivery_fee, 2),
        "total": round(total, 2),
        "eta_minutes": eta_minutes,
        "formatted_summary": f"""
Order Summary:
-------------
Restaurant: {restaurant_name}
Delivery to: {postal_code}
Scheduled delivery: {formatted_delivery_time}
Estimated arrival: {eta_minutes} minutes

Items:
{chr(10).join([f"- {item.get('name', 'Unknown item')}: £{item.get('price', 0):.2f}" for item in items])}

Subtotal: £{round(subtotal, 2)}
Discount: £{round(discount, 2)}
Delivery fee: £{round(delivery_fee, 2)}
Total: £{round(total, 2)}

Please confirm if this order summary is correct.
"""
    }
    
    return summary


@CrewBase
class ChatbotCrew:
    """Agent Eat Chatbot crew"""

    # Use relative paths for config files
    agents_config = os.path.join(Path(__file__).parent.parent, "src/config/agents.yaml")
    tasks_config = os.path.join(Path(__file__).parent.parent, "src/config/tasks.yaml")

    @agent
    def assistant(self) -> Agent:
        # Hardcoded keyword-to-result mapping for demo
        self.keyword_map = {
            "pizza": [{"name": "Margherita Pizza", "price": 10.99, "restaurant": "Pizza Place", "rating": 4.5}],
            "sushi": [{"name": "Salmon Sushi Set", "price": 15.99, "restaurant": "Sushi Bar", "rating": 4.7}],
            "burger": [{"name": "Classic Burger", "price": 9.99, "restaurant": "Burger Joint", "rating": 4.3}],
        }
        return Agent(
            config=self.agents_config["assistant"],
            verbose=True,
            tools=[
                food_search, 
                save_user_preferences, 
                search_restaurants, 
                get_restaurant_menu, 
                add_to_cart, 
                calculate_total, 
                generate_order_summary,
                process_order, 
                pay_order
            ],
        )

    @task
    def assistant_task(self) -> Task:
        return Task(config=self.tasks_config["assistant_task"], agent=self.assistant())

    @crew
    def crew(self) -> Crew:
        """Creates the chatbot crew"""

        print("Registered tools:", self.assistant().tools)

        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
