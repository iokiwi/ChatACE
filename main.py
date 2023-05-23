import os
import sys
import json
import subprocess
from argparse import ArgumentParser

import openai
from dotenv import load_dotenv
from termcolor import colored

warning = """
WARNING: This is a dangerous script. It will execute any command that the AI tells it to.

No warranty is provided. Use at your own risk.

Seriously this is dangerous and stupid. You have been warned.
"""
print(colored(warning, "red"))


load_dotenv()

parser = ArgumentParser()
parser.add_argument("objective")
parser.add_argument("--limit", default=10)
parser.add_argument("-m", "--model", default="gpt-3.5-turbo")
args = parser.parse_args()

objective = args.objective

GPT_MODEL = args.model
OPERATIONS_LIMIT = args.limit

openai.organization = os.getenv("OPENAI_ORGANIZATION")
openai.api_key = os.getenv("OPENAI_API_KEY")

initial_prompt = f"""You are a programming assistant to help programmers complete tasks in the command line.
Your goal is to "{args.objective}"

Provide the response in the following json parsable format where:
 * next_command is the bash command that use user should execute in its raw format
 * done is a boolean that indicates whether the objective has been completed


{{
    "next_command": "",
    "done": ""
}}

The response must be json parseable. Do no include any other text in the response.
"""

history = [
    {"role": "system", "content": initial_prompt},
]


def execute_bash_command(command):
    # Use subprocess.run to execute the command
    result = subprocess.run(command, text=True, capture_output=True, shell=True)
    # Return the stderr and stdout (results of the command)
    return result.stdout + result.stderr


def get_next_command(history, model, retries=3):
    okay_response = False
    retry_count = 0

    response = ""

    while retry_count < retries and okay_response is False:
        try:
            response = openai.ChatCompletion.create(
                model=model,
                messages=history
            )["choices"][0]["message"]["content"]
        except openai.error.APIError:
            print("openai.error.APIError")
            retry_count += 1
            continue
        except openai.error.RateLimitError:
            print("openai.error.RateLimitError")
            retry_count += 1
            continue

    if not response:
        print("Failed")

    return response


operations = 0
done = False
while operations < OPERATIONS_LIMIT and not done:

    response = get_next_command(history, GPT_MODEL)
    try:
        response_dict = json.loads(response)
        command = response_dict["next_command"]
        done = response_dict["done"]

        if done:
            sys.exit(0)

        print(colored(command, "blue"))
        history.append({"role": "assistant", "content": command})

        # execute command
        result = execute_bash_command(command)
        history.append({"role": "user", "content": result})
        print(result)
    except json.decoder.JSONDecodeError:
        break

    operations += 1
