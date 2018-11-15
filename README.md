# Watson Assistant Recommendation Notebook

This repository houses Watson Assistant notebooks with a set of data operation and visualization functions.

## Introduction
To help improving your Watson Assistant after you have deployed it to production, we prepared the following two Jupyter notebooks. These notebooks include practical steps for measuring, analyzing, and actively improving your virtual assistant in a continuous manner. You can use the notebooks here or from Watson Studio Community.

### Measure Notebook 
Measure notebook contains a set of automated metrics that help you monitor and understand the behavior of your system. The goal is to understand where your assistant is doing well vs where it isn’t and to potentially focus your improvement effort to one of the problem areas identified. 

### Effectiveness Notebook 
Effectiveness notebook helps you understand relative performance of each intent and entity as well as the confusion between your intents. This information helps you prioritize your improvement effort. 

## Getting Started

You can run the above notebooks locally or in [Watson Studio](https://www.ibm.com/cloud/watson-studio):

- _For running locally_

    1. Install Jupyter Notebook, see [Jupyter/IPython Notebook Quick Start Guide](https://jupyter-notebook-beginner-guide.readthedocs.io/en/latest/install.html) for more details

    2. Download Jupyter notebooks available in this repository's [notebook](https://github.com/watson-developer-cloud/assistant-improve-recommendations-notebook/tree/master/notebook) directory.

    3. Follow the instructions in each of the notebook to add Watson Assistant credentials if necessary

- _For running in Watson Studio_
    
    1. Create a Watson Studio account
    
       Sign up in [Watson Studio](https://www.ibm.com/cloud/watson-studio), or use an existing account. Lite plan is free to use.

    2. Create a new project and add a Cloud Object Storage account
    
       For more information regarding COS plans, see [Pricing](https://www.ibm.com/cloud-computing/bluemix/pricing-object-storage).

    3. Copy [Measure](https://dataplatform.cloud.ibm.com/exchange/public/entry/view/133dfc4cd1480bbe4eaa78d3f635e568) or  [Effectiveness](https://dataplatform.cloud.ibm.com/exchange/public/entry/view/133dfc4cd1480bbe4eaa78d3f636921c) notebook from Watson Studio community into your project
    
    4. Follow the instructions in each of the notebook to add project tokens and Watson Assistant credentials if necessary

## License

This library is licensed under the [Apache 2.0 license](http://www.apache.org/licenses/LICENSE-2.0).
