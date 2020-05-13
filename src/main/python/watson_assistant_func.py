import re
import json
import pandas as pd
import time
import os
import csv
import traceback


def get_assistant_definition(sdk_object, assistant_info, project=None, reset=False, filename='assistant_definition'):
    workspace_id, assistant_id, skill_id = [assistant_info.get(k) for k in ['workspace_id', 'assistant_id', 'skill_id']]

    if len(workspace_id) > 0:
        filename += '_workspace_{}.json'.format(workspace_id)
    elif len(skill_id) > 0:
        filename += '_skill_{}.json'.format(skill_id)
    else:
        print('Please provide a valid Workspace ID or Skill ID!')
        return None

    if os.path.isfile(filename) and reset is False:
        # Get file from cloud object storage
        print('Reading from file:', filename)
        with open(filename) as data:
            data_json = json.load(data)
        # Read logs into datafram
        print('Assistant definition is loaded into dataframe')
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

            # Set `export_file` to True for exporting assistant definition to json file
            if reset:
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
            print(ex)
        finally:
            log_df = pd.DataFrame(log_list)
            if len(log_list) > 0:
                print('\nWorkspace logs loaded successfully with', log_df.shape[0], 'records')
                # Write the logs to cloud object storage
                with open(filename, 'wb') as fp:
                    project.save_data(filename, log_df.to_json(orient='records'), overwrite=True)
                    # Display success message
                    print('File', fp.name, 'written successfully to COS')
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
            print(ex)
        finally:
            log_df = pd.DataFrame(log_list)
            if len(log_list) > 0:
                print('\nWorkspace logs loaded successfully with', log_df.shape[0], 'records')
                log_df.to_json(filename)
                print('File', filename, 'written successfully to local system')
            return log_df


def get_logs_filter(sdk_object, assistant_info, num_logs, filters=None, project=None, reset=False, filename=None, generate_csv=False):
    """This function calls Watson Assistant API to retrieve logs, using pagination if necessary.
       The goal is to retrieve utterances (user inputs) from the logs.
       Parameters
       ----------
       num_logs : int, the number of records to return in each page of results
       assistant_info : dict, containing information regarding sdk_object, assistant id, and name
       filters: string, a list of query filters
       reset: boolean, whether to reset log file
       filename: prefix of the name of the log file
       generate_csv: if generating a CSV of messages
       Returns
       ----------
       log_df : DataFrame of fetched logs
    """
    log_list = list()
    workspace_id, assistant_id, skill_id = [assistant_info.get(k) for k in ['workspace_id', 'assistant_id', 'skill_id']]

    if filename is None:
        filename = 'logs'
        # Create file name
        if workspace_id is not None and len(workspace_id) > 0:
            filename += '_workspace_' + workspace_id
        if assistant_id is not None and len(assistant_id) > 0:
            filename += '_assistant_' + assistant_id
            filters.append('request.context.system.assistant_id::{}'.format(assistant_id))
        if skill_id is not None and len(skill_id) > 0:
            filename += '_skill_' + skill_id
            filters.append('workspace_id::{}'.format(skill_id))
        # Remove all special characters from file name
        filename = re.sub(r'[^a-zA-Z0-9_\- .]', '', filename) + '.json'

    if (workspace_id is None or len(workspace_id) == 0) \
            and (assistant_id is None or len(assistant_id) == 0) \
            and (skill_id is None or len(skill_id) == 0):
        print('Please provide a valid Workspace ID, Assistant ID, or Skill ID!')
        return None

    if assistant_id is not None and len(assistant_id) > 0:
        filters.append('request.context.system.assistant_id::{}'.format(assistant_id))
    if skill_id is not None and len(skill_id) > 0:
        filters.append('workspace_id::{}'.format(skill_id))

    log_filter = ','.join(filters)
    log_df = None

    if project and reset is False:
        if [file['name'] for file in project.get_files() if file['name'] == filename]:
            # Get file from cloud object storage
            print('Reading from file:', filename)
            data = project.get_file(filename).getvalue().decode('utf8')
            data_json = json.loads(data)
            # Read logs into dataframe
            log_df = pd.DataFrame.from_records(data_json)
            # Display success message and return the dataframe
            print('Loaded {} logs into dataframe'.format(log_df.shape[0]))
    elif os.path.isfile(filename) and reset is False:
        # Get file from cloud object storage
        print('Reading from file:', filename)
        with open(filename) as data:
            data_json = json.load(data)
        # Read logs into dataframe
        log_df = pd.DataFrame.from_records(data_json)
        # Display success message and return the dataframe
        print('Loaded {} logs into dataframe'.format(log_df.shape[0]))
    else:
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
        finally:
            if len(log_list) > 0:
                print('\nLoading {} logs into dataframe ...'.format(len(log_list)))
                log_df = pd.DataFrame(log_list)
                print('Saving logs into {} ... '.format(filename))
                if project:
                    with open(filename, 'wb') as fp:
                        project.save_data(filename, log_df.to_json(orient='records'), overwrite=True)
                        # Display success message
                        print('File', fp.name, 'exported a project asset')
                else:
                    log_df.to_json(filename)
                    print('Completed')

    if generate_csv and log_df is not None:
        csv_filename = os.path.splitext(filename)[0] + '.csv'
        messages = [[r['input']['text']] for r in log_df['request']]
        print('\nSaving {} messages into CSV {}'.format(len(messages), csv_filename))

        with open(csv_filename, 'w') as f:
            writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            writer.writerows(messages)
            print('File', f.name, 'saved')

    return log_df