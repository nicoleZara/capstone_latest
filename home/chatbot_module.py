import openai

def generate_description(title, price):
    prompt = f"Product: {title}\nPrice: {price}\n\nDescription:"

    # Set up OpenAI API credentials
    openai.api_key = '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'  # Replace with your OpenAI API key

    # Generate description using OpenAI ChatGPT
    response = openai.Completion.create(
        engine='text-davinci-003',
        prompt=prompt,
        max_tokens=50,
        temperature=0.7,
        n=1,
        stop=None,
    )

    description = response.choices[0].text.strip()
    return description
