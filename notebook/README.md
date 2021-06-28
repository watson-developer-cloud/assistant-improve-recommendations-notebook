## Table of Contents

#### `Effectiveness Notebook.ipynb` ####
- A Jupytor notebook file. Effectiveness notebook helps you understand relative performance of each intent and entity as well as the confusion between your intents. This information helps you prioritize your improvement effort.

#### `Measure Notebook.ipynb` ####
- A Jupytor notebook file. Measure notebook contains a set of automated metrics that help you monitor and understand the behavior of your system. The goal is to understand where your assistant is doing well vs where it isn’t, and to focus your improvement effort to one of the problem areas identified.

#### `Logs Notebook.ipynb` ####
- A Jupytor notebook file. Logs notebook helps you fetch logs using Watson Assistant API.  You can fetch logs with various filters, and save them as a JSON file, or export the utterances in the logs into a CSV file.  The JSON file can be loaded into the Measure notebook.  The CSV file can be updated to Watson Assistant service for intent recommendation. Alternatively, you can run python scripts [`fetch_logs`](https://github.com/watson-developer-cloud/assistant-improve-recommendations-notebook/blob/master/src/main/python/fetch_logs.py) and [`export_csv_for_intent_recommendation`](https://github.com/watson-developer-cloud/assistant-improve-recommendations-notebook/blob/master/src/main/python/export_csv_for_intent_recommendation.py) to fetch logs and export them to [intent recommendation CSV](https://cloud.ibm.com/docs/assistant?topic=assistant-intent-recommendations#intent-recommendations-data-resources), respectively.  Run `python get_logs -h` and `python export_csv_for_intent_recommendation.py -h` for usage.  For example, to generate intent recommendation CSV from logs:

```
 # Fetch logs by keeping first user utterances in conversations with confidence `response.intents::confidence` between 0.1 and 0.6, and save to JSON file `OUTPUT_JSON_FILE`

  python src/main/python/fetch_logs.py \
  --url URL --version VERSION --apikey API_KEY --skill_id SKILL_ID --assistant_id ASSISTANT_ID \
  --filters "language::en" "request.context.system.dialog_turn_counter::1" "response.intents:confidence<0.6" "response.intents:confidence>0.1" \
  --output_json OUTPUT_JSON_FILE
  ```
```
# Take the fetch logs in `OUTPUT_JSON_FILE`, filter out utterances that is either too short (less than 3 tokens) or too long (more than 20 tokens), remove duplicates, and export them to a CSV file `OUTPUT_CSV_FILE` for intent recommendation
  
  python src/main/python/export_csv_for_intent_recommendation.py \
  --input_json OUTPUT_JSON_FILE --output_csv OUTPUT_CSV_FILE \
  --deduplicate --min_length 3 --max_length 20
  ```

#### `IBM Watson Assistant Continuous Improvement Best Practices.pdf` ####
- IBM Watson Assistant Continuous Improvement Best Practices document.

#### `data` ####
- A folder contains an example workspace with sample logs and an annotated log file for demonstration in notebooks. 

#### `imgs` ####
- A folder contains images used in notebooks.
