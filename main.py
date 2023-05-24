import os
import json
import subprocess
from argparse import ArgumentParser

import openai
from dotenv import load_dotenv
from termcolor import colored

warning = """---------------------------- WARNING ----------------------------
This is a dangerous script. It will execute any command that the
AI tells it to. No warranty is provided. Use at your own risk.
Seriously this is dangerous and stupid. You have been warned.
-----------------------------------------------------------------
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

openai.organization = os.getenv("OPENAI_ORGANIZATION").strip('"')
openai.api_key = os.getenv("OPENAI_API_KEY").strip('"')

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
    return (result.stderr.strip("\n"), result.stdout.strip("\n"))


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
            break
        except openai.error.APIError as e:
            print("openai.error.APIError")
            pass
        except openai.error.RateLimitError as e:
            print("openai.error.RateLimitError")
            pass

        retry_count += 1

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
            break

        print(colored("$ " + command, "green"))
        history.append({"role": "assistant", "content": command})

        # execute command
        stderr, stdout = execute_bash_command(command)
        history.append({"role": "user", "content": stderr + stdout})

        if stderr:
            print(colored(stderr, "red"))
        if stdout:
            print(colored(stdout, "white"))

        print()
    except json.decoder.JSONDecodeError as e:
        print("JSONDecodeError")

    operations += 1

print(colored("DONE", "green"))
