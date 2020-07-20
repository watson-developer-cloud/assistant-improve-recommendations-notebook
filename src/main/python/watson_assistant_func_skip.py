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

import re
import json
import pandas as pd
import time
import os


def get_logs(num_logs, log_list, project_creds, log_filter=None):
    """This function calls Watson Assistant API to retrieve logs, using pagination if necessary.
       The goal is to retrieve utterances (user inputs) from the logs.
       Parameters
       ----------
       num_logs : int, the number of records to return in each page of results.
       log_list : list, a list to store returned logs
       project_creds : dict, containing information on project, cos, credentials, assistant, workspace id and name
       log_filter: string, a cacheable parameter that limits the results to those matching the specified filter.

       Returns
       ----------
       log_df : Dataframe of fetched logs
    """
    # Unpack the keys from the dictionary to individual variables
    project, sdk_object, ws_id, ws_name = [project_creds.get(k) for k in ['project', 'sdk_object', 'ws_id', 'ws_name']]
    # Create file name by combining workspace name and filter
    filename = 'logs_' + ws_id + '_' + str(num_logs)

    # Remove all special characters from file name
    filename = re.sub(r'[^a-zA-Z0-9_\- .]', '', filename) + '.json'

    if [file['name'] for file in project.get_files() if file['name'] == filename]:
        # Get file from cloud object storage
        print('Reading from file:', filename)
        data = project.get_file(filename).getvalue().decode('utf8')
        data_json = json.loads(data)
        # Read logs into dataframe
        log_df = pd.DataFrame.from_records(data_json)
        # Display success message and return the dataframe
        print('Workspace logs loaded successfully with', log_df.shape[0], 'records')
        return log_df
    else:
        try:
            current_cursor = None
            while num_logs > 0:
                time.sleep(0.5)  # allow for a short break to avoid reaching rate limit
                logs_response = sdk_object.list_logs(
                    workspace_id=ws_id,
                    page_limit=500,
                    cursor=current_cursor,
                    filter=log_filter
                )
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
            print(ex)
        finally:
            log_df = pd.DataFrame(log_list)
            return log_df


def get_logs_jupyter(num_logs, log_list, workspace_creds, log_filter=None):
    """This function calls Watson Assistant API to retrieve logs, using pagination if necessary.
       The goal is to retrieve utterances (user inputs) from the logs.
       Parameters
       ----------
       num_logs : int, the number of records to return in each page of results.
       log_list : list, a list to store returned logs
       workspace_creds : dict, containing information regarding sdk_object, workspace id, and name
       log_filter: string, a cacheable parameter that limits the results to those matching the specified filter.

       Returns
       ----------
       log_df : Dataframe of fetched logs
    """
    # Unpack the keys from the dictionary to individual variables
    sdk_object, ws_id, ws_name = [workspace_creds.get(k) for k in ['sdk_object', 'ws_id', 'ws_name']]
    # Create file name by combining workspace name and filter
    filename = 'logs_' + ws_id + '_' + str(num_logs)

    # Remove all special characters from file name
    filename = re.sub(r'[^a-zA-Z0-9_\- .]', '', filename) + '.json'

    if os.path.isfile(filename):
        # Get file from cloud object storage
        print('Reading from file:', filename)
        with open(filename) as data:
            data_json = json.load(data)
        # Read logs into dataframe
        log_df = pd.DataFrame.from_records(data_json)
        # Display success message and return the dataframe
        print('Workspace logs loaded successfully with', log_df.shape[0], 'records')
        return log_df
    else:
        try:
            current_cursor = None
            while num_logs > 0:
                logs_response = sdk_object.list_logs(
                    workspace_id=ws_id,
                    page_limit=500,
                    cursor=current_cursor,
                    filter=log_filter
                )
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
            print(ex)
        finally:
            log_df = pd.DataFrame(log_list)
            return log_df
