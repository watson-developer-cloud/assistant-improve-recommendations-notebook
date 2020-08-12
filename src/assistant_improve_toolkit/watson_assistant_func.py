# coding: utf-8

# (C) Copyright IBM Corp. 2019, 2020.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import pandas as pd
import os
import csv
import traceback
import io
from string import punctuation


EN_PUNCTUATION = punctuation + '’'


def get_assistant_definition(sdk_object, assistant_info, project=None, overwrite=False, filename='assistant_definition'):
    workspace_id, assistant_id, skill_id = [assistant_info.get(k) for k in ['workspace_id', 'assistant_id', 'skill_id']]

    if len(workspace_id) > 0:
        filename += '_workspace_{}.json'.format(workspace_id)
    elif len(skill_id) > 0:
        filename += '_skill_{}.json'.format(skill_id)
    else:
        print('Please provide a valid Workspace ID or Skill ID!')
        return None

    if os.path.isfile(filename) and overwrite is False:
        # Get file from cloud object storage
        print('Reading from file:', filename)
        with open(filename) as data:
            data_json = json.load(data)
        # Read logs into dataframe
        print('Assistant definition is loaded into as a dataframe.')
        df_assistant = pd.json_normalize(data_json)
        return df_assistant
    else:
        if len(workspace_id) > 0:
            # Fetch the workspace definition
            print('Loading workspace definition using workspace id: {}'.format(workspace_id))
            assistant_definition = sdk_object.get_workspace(workspace_id=workspace_id, export=True,
                                                            include_audit=True).get_result()
        elif len(skill_id) > 0:
            # Fetch the skill definition
            print('Loading skill definition using skill id: {}'.format(skill_id))
            assistant_definition = sdk_object.get_workspace(workspace_id=skill_id, export=True,
                                                            include_audit=True).get_result()
        else:
            print('Please provide a valid Workspace ID or Skill ID!')
            assistant_definition = None

        if assistant_definition:
            # Store the workspace details in a dataframe
            df_assistant = pd.json_normalize(assistant_definition)

            # Set `overwrite` to True for exporting assistant definition to json file
            if not os.path.isfile(filename) or overwrite:
                if project is not None:
                    with open(filename, 'wb') as fp:
                        project.save_data(filename, json.dumps(assistant_definition), overwrite=True)
                        # Display success message
                        print('Definition {} exported as a project asset'.format(fp.name))
                else:
                    with open(filename, 'w') as f:
                        json.dump(assistant_definition, f)
                        print('Definition {} exported'.format(filename))

            return df_assistant
        else:
            return None


def _get_logs_from_api(sdk_object, workspace_id, log_filter, num_logs):
    log_list = list()
    try:
        current_cursor = None
        while num_logs > 0:
            if len(workspace_id) > 0:
                logs_response = sdk_object.list_logs(
                    workspace_id=workspace_id,
                    page_limit=500,
                    cursor=current_cursor,
                    filter=log_filter
                ).get_result()
            else:
                logs_response = sdk_object.list_all_logs(
                    page_limit=500,
                    cursor=current_cursor,
                    filter=log_filter
                ).get_result()
            min_num = min(num_logs, len(logs_response['logs']))
            log_list.extend(logs_response['logs'][:min_num])
            print('\r{} logs retrieved'.format(len(log_list)), end='')
            num_logs = num_logs - min_num
            current_cursor = None
            # Check if there is another page of logs to be fetched
            if 'pagination' in logs_response:
                # Get the url from which logs are to fetched
                if 'next_cursor' in logs_response['pagination']:
                    current_cursor = logs_response['pagination']['next_cursor']
                else:
                    break
    except Exception as ex:
        traceback.print_tb(ex.__traceback__)
        raise RuntimeError("Error getting logs using API.  Please check if URL/credentials are correct.")

    return log_list


def get_logs(sdk_object, assistant_info, num_logs, filename, filters=None, project=None, overwrite=False):
    """This function calls Watson Assistant API to retrieve logs, using pagination if necessary.
       The goal is to retrieve utterances (user inputs) from the logs.
       Parameters
       ----------
       num_logs : int, the number of records to return in each page of results
       assistant_info : dict, containing information regarding sdk_object, assistant id, and name
       filters: string, a list of query filters
       overwrite: boolean, whether to reset log file
       project: project io of studio project
       filename: prefix of the name of the log file
       Returns
       ----------
       log_df : DataFrame of fetched logs
    """
    if filters is None:
        filters = []

    workspace_id, assistant_id, skill_id = [assistant_info.get(k) for k in ['workspace_id', 'assistant_id', 'skill_id']]

    if (workspace_id is None or len(workspace_id) == 0) \
            and (assistant_id is None or len(assistant_id) == 0) \
            and (skill_id is None or len(skill_id) == 0):
        print('Please provide a valid Workspace ID, Assistant ID, or Skill ID!')
        return None

    # check if filename exists before retrieving logs
    file_exist = False
    if filename:
        if project:
            for file in project.get_files():
                if file['name'] == filename:
                    if not overwrite:
                        print('Load logs from existing file {}, set overwrite=True to overwrite'.format(filename))
                        return load_logs_from_file(filename, project)
                    else:
                        file_exist = True

        elif os.path.exists(filename):
            if not overwrite:
                print('Load logs from existing file {}, set overwrite=True to overwrite'.format(filename))
                return load_logs_from_file(filename, None)
            else:
                file_exist = True
    else:
        print('Please provide a valid filename.')
        return None

    # adding default filters based on assistant_id and workspace_id
    if assistant_id is not None and len(assistant_id) > 0:
        filters.append('request.context.system.assistant_id::{}'.format(assistant_id))
    if skill_id is not None and len(skill_id) > 0:
        filters.append('workspace_id::{}'.format(skill_id))

    logs = _get_logs_from_api(sdk_object=sdk_object,
                              workspace_id=workspace_id,
                              log_filter=','.join(filters),
                              num_logs=num_logs)
    print('\nLoaded {} logs'.format(len(logs)))

    if not file_exist or overwrite:
        print('Saving {} logs into JSON file... '.format(filename))
        if project:
            with open(filename, 'wb') as fp:
                project.save_data(filename, json.dumps(logs, indent=2), overwrite=overwrite)
                # Display success message
                print('File', fp.name, 'saved a project asset')
        else:
            with open(filename, 'w') as fp:
                json.dump(logs, fp, indent=2)
                print('File', fp.name, 'saved')

    return logs


def load_logs_from_file(filename, project=None):
    print('Reading from file:', filename)
    logs = None
    if project:
        # Get file from cloud object storage
        data = project.get_file(filename).getvalue().decode('utf8')
        logs = json.loads(data)
        # Read logs into dataframe
        # log_df = pd.DataFrame.from_records(data_json)
        print('Loaded {} logs'.format(len(logs)))
    else:
        if not os.path.exists(filename) or not os.path.isfile(filename):
            raise ValueError('{} either does not exist or is a directory'.format(filename))
        else:
            with open(filename) as data:
                logs = json.load(data)
            print('Loaded {} logs'.format(len(logs)))
    return logs


# From: https://github.ibm.com/watson-engagement-advisor/improve-recommendations-engine/blob/4c996b24bfcac4eb6ab6bbf39cf125cdf30b9027/src/main/python/cluster/utils.py#L44
def sanitize_text(text, remove_punctuation=True, lower=True, tokenize=True):
    text = text.strip()
    if lower:
        text = text.lower()
    # if tokenize:
    #     words = word_tokenize(text)
    # else:
    #     words = text.split()
    # if remove_punctuation:
    #     words = [word for word in words if word not in EN_PUNCTUATION]
    # return ' '.join(words)
    if remove_punctuation:
        text = text.translate(str.maketrans('', '', EN_PUNCTUATION))
    return text


def export_csv_for_intent_recommendation(logs,
                                         filename,
                                         deduplicate=True,
                                         project=None,
                                         overwrite=False,
                                         min_length=3,
                                         max_length=20):

    messages = [sanitize_text(l['request']['input']['text']) for l in logs]
    messages = filter(lambda m: min_length < len(m.split()) < max_length, messages)
    if deduplicate:
        messages = [[m] for m in set(messages)]
    else:
        messages = [[m] for m in messages]
    print('\nExporting {} messages into CSV...'.format(len(messages)))

    if project:
        with open(filename, 'wb') as fp:
            data = io.StringIO()
            writer = csv.writer(data, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            writer.writerows(messages)
            project.save_data(filename, data.getvalue(), overwrite=overwrite)
            data.close()
            # Display success message
            print('File', fp.name, 'saved a project asset')
    else:
        with open(filename, 'w') as f:
            writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            writer.writerows(messages)
            print('File', f.name, 'saved')

    return messages