# Profile Generation

This code example searches the internet for relevant information about a specific individual and compiles the collected
data into a structured HTML profile page.

## How to use

1. Set up the OPENAI api key and EXA search api key in the .env file

```bash
OPENAI_API_KEY = 'xxx'
EXA_API_KEY = 'xxx'
```

2. Run the script

```bash
python run_profile_generation.py \
  --task "xxx, Professor at xxx, find full academic profile..." \
  --whitelist http://xxx.com http://xxx.com \
  --blacklist http://xxx.com http://xxx.com

```

3. You can find the agent's complete thought process in the process_history.log file and the final generated HTML page named profile.html.

4. If you want to search information in websites need LOGIN information, please refer this camel branch https://github.com/camel-ai/camel/pull/2291

![workflow](https://github.com/user-attachments/assets/70820c77-2101-4c15-af4b-4bd06e8c5429)
