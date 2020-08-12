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

import datetime
from requests.utils import quote
import hashlib
import hmac
import pandas as pd
from contextlib import closing
from io import BytesIO
import numpy as np


def get_hash(key, msg):
    """Generates keyed-hash for a message using HMAC
        Parameters
        ----------
        key: The starting key for the hash.
        msg: message value that will be hashed
     """
    return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()


def create_signature_key(key, datestamp, region, service):
    """Create a signing key based on AWS signature version 4
        Parameters
        ----------
        key: Secret access key
        datestamp: date and timestamp
        region: service region
        service: service name
    """
    key_date = get_hash(('AWS4' + key).encode('utf-8'), datestamp)
    key_region = get_hash(key_date, region)
    key_service = get_hash(key_region, service)
    key_signing = get_hash(key_service, 'aws4_request')
    return key_signing


def generate_link(filename, project_io, expiration):
    """Generate a signing downloadable link of a file
        Parameters
        ----------
        filename: file name
        project_io: Watson Studio project io instance
        expiration: expiration time in seconds
    """
    region = ''
    http_method = 'GET'
    endpoint = project_io.get_storage_metadata()['properties']['endpoint_url']

    cur_time = datetime.datetime.utcnow()
    timestamp = cur_time.strftime('%Y%m%dT%H%M%SZ')
    datestamp = cur_time.strftime('%Y%m%d')

    standardized_querystring = ('X-Amz-Algorithm=AWS4-HMAC-SHA256' +
                                '&X-Amz-Credential=' +
                                project_io.get_storage_metadata()['properties']['credentials']['editor'][
                                    'access_key_id'] + '/' + datestamp + '/' + region +
                                '/s3/aws4_request' +
                                '&X-Amz-Date=' + timestamp +
                                '&X-Amz-Expires=' + str(expiration) +
                                '&X-Amz-SignedHeaders=host')

    standardized_querystring_url_encoded = quote(standardized_querystring, safe='&=')

    standardized_resource = '/' + project_io.get_storage_metadata()['properties']['bucket_name'] + '/' + filename

    payload_hash = 'UNSIGNED-PAYLOAD'
    standardized_headers = 'host:' + project_io.get_storage_metadata()['properties']['endpoint_url'].replace('https://',
                                                                                                             '')
    signed_headers = 'host'

    standardized_request = (http_method + '\n' +
                            standardized_resource + '\n' +
                            standardized_querystring_url_encoded + '\n' +
                            standardized_headers + '\n' +
                            '\n' +
                            signed_headers + '\n' +
                            payload_hash)

    # assemble string-to-sign
    hashing_algorithm = 'AWS4-HMAC-SHA256'
    credential_scope = datestamp + '/' + region + '/' + 's3' + '/' + 'aws4_request'
    sts = (hashing_algorithm + '\n' +
           timestamp + '\n' +
           credential_scope + '\n' +
           hashlib.sha256(standardized_request.encode('utf-8')).hexdigest())

    # generate the signature
    signature_key = create_signature_key(
        project_io.get_storage_metadata()['properties']['credentials']['editor']['secret_access_key'], datestamp,
        region, 's3')
    signature = hmac.new(signature_key,
                         sts.encode('utf-8'),
                         hashlib.sha256).hexdigest()

    # create and send the request
    request_url = (endpoint + '/' +
                   project_io.get_storage_metadata()['properties']['bucket_name'] + '/' +
                   filename + '?' +
                   standardized_querystring_url_encoded +
                   '&X-Amz-Signature=' +
                   signature)
    return request_url


def generate_excel_measure(dataframe_list, sheet_name_list, filename, project_io):
    """Generate a formatted excel file given a list of dataframes for measure notebook
        Parameters
        ----------
        dataframe_list: a list of dataframes
        sheet_name_list: a list of sheet names
        filename: output file name
        project_io: Watson Studio project io instance
    """
    with closing(BytesIO()) as output:
        writer = pd.ExcelWriter(output, engine='xlsxwriter', options={'remove_timezone': True})
        workbook = writer.book
        data_format1 = workbook.add_format({'bg_color': '#BBCCE2'})
        data_format2 = workbook.add_format({'bg_color': '#DEE6EF'})

        format_header = workbook.add_format({'text_wrap': True})

        workbook.formats[0].set_font_size(15)
        for df, name in zip(dataframe_list, sheet_name_list):
            df.to_excel(writer, sheet_name=name)
            worksheet = writer.sheets[name]
            worksheet.set_row(0, 30, format_header)
            worksheet.set_column('A:A', 5)
            worksheet.set_column('B:B', 30)
            worksheet.set_column('C:C', 30)
            worksheet.set_column('D:D', 15)
            worksheet.set_column('F:G', 35)
            worksheet.set_column('H:AH', 20)
            for row in range(1, len(df) + 1, 2):
                worksheet.set_row(row, cell_format=data_format1)
                worksheet.set_row(row + 1, cell_format=data_format2)
        writer.save()
        if project_io is not None:
            project_io.save_data(filename, output.getvalue(), overwrite=True)
        else:
            with open(filename, 'wb') as out:
                out.write(output.getvalue())


def generate_excel_effectiveness(dataframe_list, sheet_name_list, filename, project_io):
    """Generate a formatted excel file given a list of dataframes for effectiveness notebook
        Parameters
        ----------
        dataframe_list: a list of dataframes
        sheet_name_list: a list of sheet names
        filename: output file name
        project_io: Watson Studio project io instance
    """
    with closing(BytesIO()) as output:
        writer = pd.ExcelWriter(output, engine='xlsxwriter', options={'remove_timezone': True})
        workbook = writer.book
        data_format1 = workbook.add_format({'bg_color': '#BBCCE2'})
        data_format2 = workbook.add_format({'bg_color': '#DEE6EF'})

        format_header = workbook.add_format({'text_wrap': True})

        workbook.formats[0].set_font_size(15)
        for df, name in zip(dataframe_list, sheet_name_list):
            df.to_excel(writer, sheet_name=name)
            worksheet = writer.sheets[name]
            worksheet.set_row(0, 20, format_header)
            worksheet.set_column('A:A', 5)
            worksheet.set_column('B:D', 30)
            for row in range(1, len(df) + 1, 2):
                worksheet.set_row(row, cell_format=data_format1)
                worksheet.set_row(row + 1, cell_format=data_format2)
        writer.save()
        if project_io is not None:
            project_io.save_data(filename, output.getvalue(), overwrite=True)
        else:
            with open(filename, 'wb') as out:
                out.write(output.getvalue())


def export_result_excel(df_effective, sample_size=100, project_io=None):
    if df_effective.size == 0:
        print('No ineffective conversations found in logs')
        return
    # Copy the effective dataframe
    df_excel = df_effective.copy(deep=True)
    # Rename columns to generate excel
    df_excel = df_excel.rename(columns={'log_id': 'Log ID', 'response.context.conversation_id': 'Conversation ID',
                                        'response.timestamp': 'Response Timestamp',
                                        'request_input': 'Utterance Text',
                                        'response_text': 'Response Text',
                                        'response.top_intent_intent': 'Detected top intent',
                                        'response.top_intent_confidence': 'Detected top intent confidence',
                                        'Intent 2 intent': 'Intent 2', 'Intent 2 confidence': 'Intent 2 Confidence',
                                        'Intent 3 intent': 'Intent 3', 'Intent 3 confidence': 'Intent 3 Confidence',
                                        'response_entities': 'Detected Entities',
                                        'Escalated_conversation': 'Escalated conversation?',
                                        'Covered': 'Covered?', 'Not Covered cause': 'Not covered - cause',
                                        'response.output.nodes_visited_s': 'Dialog Flow',
                                        'response_dialog_stack': 'Dialog stack',
                                        'response_dialog_request_counter': 'Dialog request counter',
                                        'response_dialog_turn_counter': 'Dialog turn counter'
                                        })

    existing_columns = ['Log ID', 'Conversation ID', 'Response Timestamp', 'Customer ID (must retain for delete)',
                        'Utterance Text', 'Response Text', 'Detected top intent', 'Detected top intent confidence',
                        'Intent 2', 'Intent 2 Confidence', 'Confidence gap (between 1 and 2)', 'Intent 3',
                        'Intent 3 Confidence',
                        'Detected Entities', 'Escalated conversation?', 'Covered?', 'Not covered - cause',
                        'Dialog Flow', 'Dialog stack', 'Dialog request counter', 'Dialog turn counter']
    # Add new columns for annotating problematic logs
    new_columns_excel = ['Response Correct (Y/N)?', 'Response Helpful (Y/N)?',
                         'Root cause (Problem with Intent, entity, dialog)',
                         'Wrong intent? If yes, put the correct intent. Otherwise leave it blank',
                         'New intent needed? (A new intent. Otherwise leave blank)',
                         'Add Utterance to Training data (Y/N)',
                         'Entity missed? If yes, put the missed entity value. Otherwise leave it blank',
                         'New entity needed? If yes, put the entity name',
                         'New entity value? If yes, put the entity value', 'New dialog logic needed?',
                         'Wrong dialog node? If yes, put the node name. Otherwise leave it blank',
                         'No dialog node triggered']

    # Add the new columns to the dataframe
    df_excel = df_excel.reindex(columns=[*existing_columns, *new_columns_excel], fill_value='')

    # Set output filename
    all_file = 'All.xlsx'
    escalated_sample_file = 'Escalated_sample.xlsx'
    non_escalated_sample_file = 'NotEscalated_sample.xlsx'

    # Remove timezone infomation
    df_excel['Response Timestamp'] = df_excel['Response Timestamp'].dt.tz_localize(None)

    # Prepare dataframe containing all utterances sorted by Conversation ID and Response Timestamp
    df_all = df_excel.sort_values(by=['Conversation ID', 'Response Timestamp']).reset_index(drop=True)

    # Prepare dataframe containing covered utterances sorted by Conversation ID and Response Timestamp
    df_covered = df_excel[df_excel['Covered?']==True].sort_values(
        by=['Conversation ID', 'Response Timestamp']).reset_index(drop=True)

    # Prepare dataframe containing not covered utterances sorted by Conversation ID and Response Timestamp
    df_not_covered = df_excel[df_excel['Covered?']==False].sort_values(
        by=['Conversation ID', 'Response Timestamp']).reset_index(drop=True)

    # Convert to Excel format and save to local or upload to COS if project_io is provided
    generate_excel_measure([df_all, df_covered, df_not_covered],
                           ['All_Utterances', 'Covered_Utterances', 'Not_Covered_Utterances'], filename=all_file,
                           project_io=project_io)

    # Prepare dataframe containing escalated conversations
    df_escalated_true = df_excel.loc[df_excel['Escalated conversation?']==True]

    # Sample escalated conversations
    if sample_size > 0 and len(df_escalated_true) > 0:
        # Get unique escalated conversation ids
        conversation_ids = df_escalated_true['Conversation ID'].unique()
        sampled_conversation_ids = np.random.choice(conversation_ids, sample_size)
        df_escalated_true = df_escalated_true[
            df_escalated_true['Conversation ID'].isin(sampled_conversation_ids)].sort_values(
            by=['Conversation ID', 'Response Timestamp']).reset_index(drop=True)

    # Prepare dataframe containing covered utterances in escalated conversations sorted by Conversation ID and Response Timestamp
    df_escalated_covered = df_escalated_true[df_escalated_true['Covered?']==True].reset_index(drop=True)

    # Prepare dataframe containing not covered utterances in escalated conversations sorted by Conversation ID and Response Timestamp
    df_escalated_not_covered = df_escalated_true[df_escalated_true['Covered?']==False].reset_index(drop=True)

    # Covert to Excel format and upload to COS
    generate_excel_measure([df_escalated_true, df_escalated_covered, df_escalated_not_covered],
                           ['All_Utterances', 'Covered_Utterances', 'Not_Covered_Utterances'],
                           filename=escalated_sample_file, project_io=project_io)

    # Prepare dataframe containing non-escalated conversations
    df_not_escalated = df_excel.loc[df_excel['Escalated conversation?']==False].reset_index(drop=True)

    # Sample escalated conversations
    if sample_size > 0:
        # Get unique non-escalated conversation ids
        conversation_ids = df_not_escalated['Conversation ID'].unique()
        sampled_conversation_ids = np.random.choice(conversation_ids, sample_size)
        df_not_escalated = df_not_escalated[
            df_not_escalated['Conversation ID'].isin(sampled_conversation_ids)].sort_values(
            by=['Conversation ID', 'Response Timestamp']).reset_index(drop=True)

    # Prepare dataframe containing covered utterances in escalated conversations sorted by Conversation ID and Response Timestamp
    df_not_escalated_covered = df_not_escalated[df_not_escalated['Covered?']==True].reset_index(drop=True)

    # Generate not escalated and not covered sample file
    df_not_escalated_not_covered = df_not_escalated[df_not_escalated['Covered?']==False].reset_index(drop=True)

    # Covert to Excel format and upload to COS
    generate_excel_measure([df_not_escalated, df_not_escalated_covered, df_not_escalated_not_covered],
                           ['All_Utterances', 'Covered_Utterances', 'Not_Covered_Utterances'],
                           filename=non_escalated_sample_file, project_io=project_io)
