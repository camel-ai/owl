# Profile Generation

This code example searches the internet for relevant information about a specific individual and compiles the collected
data into a structured HTML profile page.

## How to use

1. Set up the OPENAI api key in the .env file

```bash
OPENAI_API_KEY = 'xxx'
```

2. Run the script

```bash
python run_profile_generation.py --task "Ahmed Eltawil, Professor at KAUST, Suggested Websites:..."
```

3. You can find the entire thought process of the agent within the log file.

4. If you want to search information in websites need LOGIN information, please refer this camel branch https://github.com/camel-ai/camel/pull/2291
![workflow](https://github.com/user-attachments/assets/9861705a-50b7-4e53-85e2-31397f285a73)
