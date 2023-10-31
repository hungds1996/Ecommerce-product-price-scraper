import json
import re 
from requests import post

def save_results(results: dict):
    data = {"results": results}
    with open("./results.json", "w") as f:
        json.dump(data, f)
        

def post_results(results, endpoint, search_text, source):
    headers = {
        "Content-Type": "application/json"
    }
    data = {"data": results, "search_text": search_text, "source": source}
    
    print("Sending request to ", endpoint)
    response = post("http://127.0.0.1:5000"+endpoint, headers=headers, json=data)
    print("Status code: ", response.status_code)


def handle_name(name: str) -> str:
    text = name.split("\n")[0]
    return re.sub("[\(\[].*?[\)\]]", "", text)


def handle_price(price: str):
    price = price.replace('₫', '').replace('.', '')
    if "-" in price:
        bounds = price.split(" - ")
    else:
        if "\n" in price:
            price = price.split("\n")[-1]
        bounds = ["0", price]
    return bounds