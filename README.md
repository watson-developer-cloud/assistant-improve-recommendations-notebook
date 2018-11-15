# Watson Assistant Recommendation Notebook

This repository houses Watson Assistant notebooks with a set of data operation and visualization functions.

## Introduction
To help improving your Watson Assistant after you have deployed it to production, we prepared the following two Jupyter notebooks. These notebooks include practical steps for measuring, analyzing, and actively improving your virtual assistant in a continuous manner. You can use the notebooks here or from Watson Studio Community.

### Measure Notebook 
Measure notebook contains a set of automated metrics that help you monitor and understand the behavior of your system. The goal is to understand where your assistant is doing well vs where it isn’t and to potentially focus your improvement effort to one of the problem areas identified. 

### Effectiveness Notebook 
Effectiveness notebook helps you understand relative performance of each intent and entity as well as the confusion between your intents. This information helps you prioritize your improvement effort. 

## Getting Started

1. Create a Watson Studio account
    
    Sign up in [Watson Studio](https://www.ibm.com/cloud/watson-studio), or use an existing account. Lite plan is free to use.

2. Create a new project and add a Cloud Object Storage account
    
    For more information regarding COS plans, see [Pricing](https://www.ibm.com/cloud-computing/bluemix/pricing-object-storage).

3. Load Measure or Effectiveness notebook from Watson Studio community
    
    - Measure notebook: [link](https://dataplatform.cloud.ibm.com/exchange/public/entry/view/133dfc4cd1480bbe4eaa78d3f635e568)
    - Effectiveness notebook: [link](https://dataplatform.cloud.ibm.com/exchange/public/entry/view/133dfc4cd1480bbe4eaa78d3f636921c)

4. Follow the instruction in each of the notebook to add project tokens and Watson Assistant credentials if necessary.

5. You can now run the notebook

Check the [Watson Studio documentation](https://dataplatform.cloud.ibm.com/docs/content/analyze-data/notebooks-parent.html?audience=wdp&context=wdp) for more details.

## License

This library is licensed under the [Apache 2.0 license](http://www.apache.org/licenses/LICENSE-2.0).
