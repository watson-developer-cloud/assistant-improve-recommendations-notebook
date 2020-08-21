# Watson Assistant Improve Notebooks

This repository houses Watson Assistant Improve notebooks and the underlying assistant improve toolkit library.

## Introduction
To help improving your Watson Assistant after you have deployed it to production, we prepared the following four Jupyter notebooks. These notebooks include practical steps for measuring, analyzing, and actively improving your assistant in a continuous manner. Check out [IBM Watson Assistant Continuous Improvement Best Practices](https://github.com/watson-developer-cloud/assistant-improve-recommendations-notebook/raw/master/notebook/IBM%20Watson%20Assistant%20Continuous%20Improvement%20Best%20Practices.pdf) for more details.

### Measure Notebook 
The Measure notebook contains a set of automated metrics that help you monitor and understand the behavior of your system. The goal is to understand where your assistant is doing well vs where it isn’t, and to focus your improvement effort to one of the problem areas identified. 

### Effectiveness Notebook 
The Effectiveness notebook helps you understand relative performance of each intent and entity as well as the confusion between your intents. This information helps you prioritize your improvement effort. 

### Customer Effort Notebook 
The Effectiveness notebook helps you measure and analyze the performance improvement after enabling the [Disambiguation](https://cloud.ibm.com/docs/assistant?topic=assistant-dialog-runtime#dialog-runtime-disambiguation) and [Autolearning](https://cloud.ibm.com/docs/assistant?topic=assistant-autolearn) features

### Logs Notebook
The Logs notebook helps you fetch logs using Watson Assistant API.  You can fetch logs with various filters, and save them as a JSON file, or export the utterances in the logs into a CSV file.  The JSON file can be loaded into the Measure notebook.  The CSV file can be used for [intent recommendation service](https://cloud.ibm.com/docs/assistant?topic=assistant-intent-recommendations#intent-recommendations-get-intent-recommendations-task). Alternatively, you can run python scripts [`fetch_logs`](https://github.com/watson-developer-cloud/assistant-improve-recommendations-notebook/blob/master/src/main/python/fetch_logs.py) and [`export_csv_for_intent_recommendation`](https://github.com/watson-developer-cloud/assistant-improve-recommendations-notebook/blob/master/src/main/python/export_csv_for_intent_recommendation.py) to fetch logs and export them to [intent recommendation CSV](https://cloud.ibm.com/docs/assistant?topic=assistant-intent-recommendations#intent-recommendations-data-resources), respectively.  Run `python get_logs -h` and `python export_csv_for_intent_recommendation.py -h` for usage.  For example, to generate intent recommendation CSV from logs:

- Fetch logs by keeping first user utterances in conversations with confidence `response.intents::confidence` between 0.1 and 0.6, and save to JSON file `OUTPUT_JSON_FILE`
  ```angular2
  python src/main/python/fetch_logs.py \
  --url URL --version VERSION --apikey API_KEY --skill_id SKILL_ID --assistant_id ASSISTANT_ID \
  --filters "language::en" "request.context.system.dialog_turn_counter::1" "response.intents:confidence<0.6" "response.intents:confidence>0.1" \
  --output_json OUTPUT_JSON_FILE
  ```
- Take the fetch logs in `OUTPUT_JSON_FILE`, filter out utterances that is either too short (less than 3 tokens) or too long (more than 20 tokens), remove duplicates, and export them to a CSV file `OUTPUT_CSV_FILE` for intent recommendation
  ```angular2
  python src/main/python/export_csv_for_intent_recommendation.py \
  --input_json OUTPUT_JSON_FILE --output_csv OUTPUT_CSV_FILE \
  --deduplicate --min_length 3 --max_length 20
  ```
  The CSV file `OUTPUT_CSV_FILE` can be used as [intent recommendation data source](https://cloud.ibm.com/docs/assistant?topic=assistant-intent-recommendations#intent-recommendations-data-resources).

## Getting Started

You can run the notebooks locally or in [Watson Studio](https://dataplatform.cloud.ibm.com/docs/content/wsj/analyze-data/notebooks-parent.html).

- _**Run locally**_

    1. Install Jupyter Notebook, see [Jupyter/IPython Notebook Quick Start Guide](https://jupyter-notebook-beginner-guide.readthedocs.io/en/latest/install.html) for more details.

    2. Download the Jupyter notebooks available in this repository's [notebook](https://github.com/watson-developer-cloud/assistant-improve-recommendations-notebook/tree/master/notebook) directory. 
    
       - [Measure Notebook.ipynb](https://github.com/watson-developer-cloud/assistant-improve-recommendations-notebook/blob/master/notebook/Measure%20Notebook.ipynb)
       - [Effectiveness Notebook.ipynb](https://github.com/watson-developer-cloud/assistant-improve-recommendations-notebook/blob/master/notebook/Effectiveness%20Notebook.ipynb)
       - [Logs Notebook.ipynb](https://github.com/watson-developer-cloud/assistant-improve-recommendations-notebook/blob/master/notebook/Logs%20Notebook.ipynb)
       
       __Note: These notebook files are not designed for Watson Studio environment__
       
    3. Install dependencies with `pip install -r requirements.txt`

    4. Follow the instructions in each of the notebooks. Be sure to add your Watson Assistant credentials if necessary.

- _**Run in Watson Studio**_
    
    1. Create a Watson Studio account.
    
       Sign up in [Watson Studio](https://www.ibm.com/cloud/watson-studio), or use an existing account. Lite plan is free to use.

    2. Create a new project and add a Cloud Object Storage (COS) account.
    
       For more information regarding COS plans, see [Pricing](https://www.ibm.com/cloud-computing/bluemix/pricing-object-storage).

    3. Copy [Measure](https://dataplatform.cloud.ibm.com/exchange/public/entry/view/133dfc4cd1480bbe4eaa78d3f635e568) or  [Effectiveness](https://dataplatform.cloud.ibm.com/exchange/public/entry/view/133dfc4cd1480bbe4eaa78d3f636921c) notebook from Watson Studio community into your project.
    
    4. Follow the instructions in each notebook to add project tokens and Watson Assistant credentials if necessary.

## Contributing 
See [CONTRIBUTING.md](CONTRIBUTING.md) and [DEVELOPER.MD](DEVELOPER.MD) for more details on how to contribute

## License
This library is licensed under the [Apache 2.0 license](http://www.apache.org/licenses/LICENSE-2.0).

