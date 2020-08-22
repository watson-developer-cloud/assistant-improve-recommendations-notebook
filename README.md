# Watson Assistant Improve Notebooks

[![Build Status](https://travis-ci.org/watson-developer-cloud/assistant-improve-recommendations-notebook.svg?branch=master)](https://travis-ci.org/github/watson-developer-cloud/assistant-improve-recommendations-notebook)
[![Slack](https://wdc-slack-inviter.mybluemix.net/badge.svg)](https://wdc-slack-inviter.mybluemix.net)
[![Latest Stable Version](https://img.shields.io/pypi/v/assistant-improve-toolkit)](https://pypi.org/project/assistant-improve-toolkit/)
[![CLA assistant](https://cla-assistant.io/readme/badge/watson-developer-cloud/assistant-improve-recommendations-notebook)](https://cla-assistant.io/watson-developer-cloud/assistant-improve-recommendations-notebook)

This repository houses Watson Assistant Improve notebooks and the underlying assistant improve toolkit library.

## Introduction
To help improving your Watson Assistant after you have deployed it to production, we prepared the following Jupyter notebooks. These notebooks include practical steps for measuring, analyzing, and actively improving your assistant in a continuous manner. Check out [IBM Watson Assistant Continuous Improvement Best Practices](https://github.com/watson-developer-cloud/assistant-improve-recommendations-notebook/raw/master/notebook/IBM%20Watson%20Assistant%20Continuous%20Improvement%20Best%20Practices.pdf) for more details.

- __Measure notebook__ contains a set of automated metrics that help you monitor and understand the behavior of your system. The goal is to understand where your assistant is doing well vs where it isn’t, and to focus your improvement effort to one of the problem areas identified. 

- __Effectiveness notebook__ helps you understand relative performance of each intent and entity as well as the confusion between your intents. This information helps you prioritize your improvement effort. 

- __Customer Effort notebook__ helps you measure and analyze the performance improvement after enabling the [Disambiguation](https://cloud.ibm.com/docs/assistant?topic=assistant-dialog-runtime#dialog-runtime-disambiguation) and [Autolearning](https://cloud.ibm.com/docs/assistant?topic=assistant-autolearn) features

- __Logs notebook__ helps you fetch logs using Watson Assistant API.  You can fetch logs with various filters, and save them as a JSON file, or export the utterances in the logs into a CSV file.  The JSON file can be loaded into the Measure notebook.  The CSV file can be used for [intent recommendation service](https://cloud.ibm.com/docs/assistant?topic=assistant-intent-recommendations#intent-recommendations-get-intent-recommendations-task). Alternatively, you can run python scripts [`fetch_logs`](https://github.com/watson-developer-cloud/assistant-improve-recommendations-notebook/blob/master/src/main/python/fetch_logs.py) and [`export_csv_for_intent_recommendation`](https://github.com/watson-developer-cloud/assistant-improve-recommendations-notebook/blob/master/src/main/python/export_csv_for_intent_recommendation.py) to fetch logs and export them to [intent recommendation CSV](https://cloud.ibm.com/docs/assistant?topic=assistant-intent-recommendations#intent-recommendations-data-resources), respectively.  Run `python get_logs -h` and `python export_csv_for_intent_recommendation.py -h` for usage. 

- __Dialog Flow Analysis notebook__ help you assess and analyze user journeys and issues related to the dialog flow of ineffective (low quality) conversations based on production logs. Check out [Dialog Flow Analysis](https://github.com/watson-developer-cloud/assistant-dialog-flow-analysis) for more details.

- __Dialog Skill Analysis notebook__ help you analyze characteristics of your data such as the number of training examples for each intent or the terms which seem to be characteristic of a specific intent. Check out [Dalog Skill Analysis](https://github.com/watson-developer-cloud/assistant-dialog-skill-analysis) for more details.

## Getting Started

You can either run the notebooks locally or in [IBM Watson Studio](https://dataplatform.cloud.ibm.com/docs/content/wsj/analyze-data/notebooks-parent.html).

- **Run locally**

    1. Install Jupyter Notebook, see [Jupyter/IPython Notebook Quick Start Guide](https://jupyter-notebook-beginner-guide.readthedocs.io/en/latest/install.html) for more details.
    2. Download the Jupyter notebooks available in this repository's [notebook](https://github.com/watson-developer-cloud/assistant-improve-recommendations-notebook/tree/master/notebook) directory. __Note: These notebook files are not designed for Watson Studio environment__
    3. Start jupyter server `jupyter notebook`
    4. Follow the instructions in each of the notebooks. Be sure to add your Watson Assistant credentials if necessary.

- **Run in Watson Studio**
    
    1. Create a Watson Studio account.    
       Sign up in [Watson Studio](https://www.ibm.com/cloud/watson-studio), or use an existing account. Lite plan is free to use.

    2. Create a new project and add a Cloud Object Storage (COS) account.    
       For more information regarding COS plans, see [Pricing](https://www.ibm.com/cloud-computing/bluemix/pricing-object-storage).

    3. Copy [Measure](https://dataplatform.cloud.ibm.com/exchange/public/entry/view/133dfc4cd1480bbe4eaa78d3f635e568) or  [Effectiveness](https://dataplatform.cloud.ibm.com/exchange/public/entry/view/133dfc4cd1480bbe4eaa78d3f636921c) notebook from Watson Studio community into your project.
    
    4. Follow the instructions in each notebook to add project tokens and Watson Assistant credentials if necessary.

## Guides
* Learn more about our measure and effectiveness notebook on Medium: [Continuously Improve Your Watson Assistant with Jupyter Notebooks](https://medium.com/ibm-watson/continuously-improve-your-watson-assistant-with-jupiter-notebooks-60231df4f01f)

## Contributing 
See [CONTRIBUTING.md](CONTRIBUTING.md) for more details on how to contribute

## License
This library is licensed under the [Apache 2.0 license](http://www.apache.org/licenses/LICENSE-2.0).

