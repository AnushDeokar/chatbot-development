import textbase
from textbase.message import Message
from textbase import models
import os
from typing import List
import openai
import json
import requests
import datetime
# Load your OpenAI API key
# or from environment variable:
models.OpenAI.api_key = os.getenv("OPENAI_API_KEY")

# Prompt for GPT-3.5 Turbo
SYSTEM_PROMPT = """You are chatting with an AI. There are no specific prefixes for responses, so you can ask or talk about anything you like. The AI will respond in a natural, conversational manner. Feel free to start the conversation with any question or topic, and let's have a pleasant chat!
"""

def get_stock_info(name):
    url = "https://twelve-data1.p.rapidapi.com/stocks"

    querystring = {"exchange":name,"format":"json"}

    headers = {
        "X-RapidAPI-Key": os.getenv("RAPID_API_KEY"),
        "X-RapidAPI-Host": "twelve-data1.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)


    return json.dumps(response)

def get_flight_info(loc_origin, loc_destination):
    url = "https://travel-advisor.p.rapidapi.com/locations/v2/auto-complete"

    querystring = {"query":loc_origin+"&"+loc_destination,"lang":"en_US","units":"km"}

    headers = {
        "X-RapidAPI-Key": os.getenv("RAPID_API_KEY"),
        "X-RapidAPI-Host": "travel-advisor.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)

    return json.dumps(response)


def get_news_info(location):
    url = "https://lexper.p.rapidapi.com/v1.1/extract"
    querystring = {"url":location,"js_timeout":"30","media":"true"}

    headers = {
        "X-RapidAPI-Key": os.getenv("RAPID_API_KEY"),
        "X-RapidAPI-Host": "lexper.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)

    return json.dumps(response)

def get_weather_info(location):
    url = f'http://api.weatherstack.com/current?access_key={os.getenv("RAPID_API_KEY")}&query={location}'
    weather_info2 = requests.get(url).json()
    weather_info = {
        "location":location,
        "current": weather_info2["current"]
    }
    return json.dumps(weather_info)

def get_movie_info(name):
    url = "https://mdblist.p.rapidapi.com/"

    querystring = {"s":name}

    headers = {
        "X-RapidAPI-Key": os.getenv("RAPID_API_KEY"),
        "X-RapidAPI-Host": "mdblist.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)
    return json.dumps(response)


@textbase.chatbot("talking-bot")
def on_message(message_history: List[Message], state: dict = None):

    msg_content = message_history[len(message_history)-1].content

    messages=[{"role": "user", "content": msg_content}]

    function_descriptions = [
    {
        "name": "get_flight_info",
        "description": "Get flight information between two locations",
        "parameters": {
            "type": "object",
            "properties": {
                "loc_origin": {
                    "type": "string",
                    "description": "The departure airport, e.g. DUS",
                },
                "loc_destination": {
                    "type": "string",
                    "description": "The destination airport, e.g. HAM",
                },
            },
            "required": ["loc_origin", "loc_destination"],
        },
    },
    {
        "name": "get_news_info",
        "description": "Get current news of any location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "location for which you want news",
                },
            },
            "required": ["location"],
        },
    },
    {
        "name": "get_weather_info",
        "description": "Get weather info of any location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "Location for which we want to know the weather",
                },
            },
            "required": ["location"],
        },
    },
    {
        "name": "get_stock_info",
        "description": "Get current stock info of any company",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "company name",
                },
            },
            "required": ["name"],
        },
    },
    {
        "name": "get_movie_info",
        "description": "Get info of any movie",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "name of movie",
                },
            },
            "required": ["name"],
        },
    }

    ]


    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        functions=function_descriptions,
        function_call="auto",
    )

    res_msg = completion["choices"][0]["message"]

    msg_content = None
    if res_msg.get("function_call"):
        available_functions = {
            "get_flight_info": get_flight_info,
            "get_weather_info":get_weather_info,
            "get_stock_info": get_stock_info,
            "get_news_info": get_news_info,
            "get_movie_info": get_movie_info
        }
        func_name = res_msg["function_call"]["name"]
        function_to_call = available_functions[func_name]
        func_args = json.loads(res_msg["function_call"]["arguments"])

        if (func_name=="get_weather_info"):
            func_response = function_to_call(
                location=func_args.get("location")
            )
        elif(func_name=="get_stock_info"):
            func_response = function_to_call(
                name=func_args.get("name")
            )
        elif(func_name=="get_news_info"):
            func_response = function_to_call(
                location=func_args.get("location")
            )
        elif(func_name=="get_movie_info"):
            func_response = function_to_call(
                name=func_args.get("name")
            )
        elif(func_name=="get_flight_info"):
            func_response = function_to_call(
               loc_origin = func_args.get("loc_origin"), 
               loc_destination=func_args.get("loc_destination")
            )
        
        messages.append(res_msg)
        messages.append({
            "role": "function",
            "name": func_name,
            "content": func_response
        })


        second_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
        )

        if state is None or "counter" not in state:
            state = {"counter": 0}
        else:
            state["counter"] += 1
        msg_content =  second_response
        return second_response["choices"][0]["message"]["content"], state

    if state is None or "counter" not in state:
        state = {"counter": 0}
    else:
        state["counter"] += 1

    # # # Generate GPT-3.5 Turbo response
    bot_response_str = models.OpenAI.generate(
        system_prompt=SYSTEM_PROMPT,
        message_history=message_history,
        model="gpt-3.5-turbo",
    )


    return bot_response_str, state
