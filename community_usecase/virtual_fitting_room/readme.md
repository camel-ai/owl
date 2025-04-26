# Virtual Fitting Room
## What's this?

This code example can automatically search for suitable trending products from your designated websites (e.g. Uniqlo) and show you realistic try-on effects with different virtual models (you can also use your own photo as the model to get a more intuitive try-on experience).

All with one prompt 🪄

## Dependencies:

 1. I made some modifications to the camel repo so please first run "git clone -b feature/virtual-try-on-toolkit-and-partial-screenshot --single-branch https://github.com/camel-ai/camel.git"
 2. fill in your klingai api keys for virtual try-on in camel/toolkits/virtual_try_on_toolkit.py (you can get it from https://klingai.kuaishou.com/dev-center)
 3. pip install the above cloned repo

## How to use: 
 1. copy "run_gpt4o.py" to owl/examples
 2. run "python examples/run_gpt4o.py" (assuming your current dir is owl)
 3. the fetched image of clothes will be saved in tmp/clothes
 4. the final try-on image will be saved in tmp/fitting_room

 ## Example Output
 https://drive.google.com/file/d/1J3caeAL4C-_LEULPi6VOvlyJPazQeOOv/view?usp=sharing

 (click the above link to see the screen recording, which shows the full automated process from browsing clothes on uniqlo to generating the final try-on image)