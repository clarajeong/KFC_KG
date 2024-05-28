# The API key of this code must be secure
from openai import AzureOpenAI

gptmodel = 'gpt-4-1106-Preview' # 'gpt-35-turbo-0613', 'gpt-35-turbo-1106', 'gpt-4-0613', 'gpt-4-1106-Preview'

def inference_azure(prompt, model_name = gptmodel):
    client = AzureOpenAI(
        api_key="ddb53a61fc64445da04a29e3d126d6a8",
        api_version="2023-09-01-preview",
        azure_endpoint="https://jiho-3.openai.azure.com/",
    )

    completion = client.chat.completions.create(
        model=model_name,
        messages=[
            {
                "role": "user",
                "content": prompt,
            },
        ],

    )
    # print(completion.model_dump_json(indent=2))
    return completion.choices[0].message.content.strip()
