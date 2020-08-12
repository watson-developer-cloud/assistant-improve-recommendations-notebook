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

import argparse
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_watson import AssistantV1

from watson_assistant_func import get_logs


def parse_args():
    parser = argparse.ArgumentParser(description='Script to fetch logs from Watson Assistant service.')

    # Required arguments
    parser.add_argument(
        "--url",
        type=str,
        required=True,
        help="Watson Asssistant Legacy V1 URLs, for example, https://api.us-east.assistant.watson.cloud.ibm.com."
    )
    parser.add_argument(
        "--version",
        type=str,
        required=True,
        help="API requests require a version parameter that takes a date in the format version=YYYY-MM-DD. When we "
             "change the API in a backwards-incompatible way, we release a new version date. "
    )
    parser.add_argument(
        "--apikey",
        type=str,
        required=True,
        help="The IAM token."
    )

    # Optional arguments
    parser.add_argument(
        "--workspace_id",
        type=str,
        default='',
        help="To load the skill of an assistant in the next section, you need to provide either Workspace ID or Skill "
             "ID. The values can be found on the View API Details page. If you are using versioning in Watson "
             "Assistant, this ID represents the Development version of your skill definition.",
    )
    parser.add_argument(
        "--skill_id",
        type=str,
        default='',
        help="To load the skill of an assistant in the next section, you need to provide either Workspace ID or Skill "
             "ID. The values can be found on the View API Details page. If you are using versioning in Watson "
             "Assistant, this ID represents the Development version of your skill definition.",
    )
    parser.add_argument(
        "--assistant_id",
        type=str,
        default='',
        help="To load the skill of an assistant in the next section, you need to provide Assistant ID. The values can "
             "be found on the View API Details page.",
    )
    parser.add_argument(
        '--filters',
        default=[],
        nargs='*',
        help="List of filters (string), separated by space.  For example, '--filters language::en "
             "meta.summary.input_text_length_i>0 response_timestamp>=2020-03-01'",
    )
    parser.add_argument(
        '--num_logs',
        type=int,
        default=20000,
        help="Number of logs to retrieve (default=20000)",
    )
    parser.add_argument(
        '--output_json',
        type=str,
        default=None,
        help="If output_json is set, logs will be saved to filename as a JSON file",
    )
    parser.add_argument(
        '--overwrite',
        type=bool,
        default=False,
        help="If overwrite filename if it exists",
    )

    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    print(vars(args))

    authenticator = IAMAuthenticator(args.apikey)
    sdk_object = AssistantV1(version=args.version, authenticator=authenticator)
    sdk_object.set_service_url(args.url)

    assistant_information = {'workspace_id': args.workspace_id,
                             'skill_id': args.skill_id,
                             'assistant_id': args.assistant_id}
    print(assistant_information)

    logs = get_logs(sdk_object,
                    assistant_information,
                    num_logs=args.num_logs,
                    filename=args.output_json,
                    filters=args.filters,
                    project=None,
                    overwrite=args.overwrite,
                    )
