# Licensed to the StackStorm, Inc ('StackStorm') under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from st2client.commands import resource
from st2client.formatters import table
from st2client.models import TriggerInstance
from st2client.utils.date import format_isodate


class TriggerInstanceResendCommand(resource.ResourceCommand):
    def __init__(self, resource, *args, **kwargs):

        super(TriggerInstanceResendCommand, self).__init__(
            resource, kwargs.pop('name', 're-emit'),
            'A command to re-emit a particular trigger instance.',
            *args, **kwargs)

        self.parser.add_argument('id', nargs='?',
                                 metavar='id',
                                 help='ID of trigger instance to re-emit.')
        self.parser.add_argument(
            '-h', '--help',
            action='store_true', dest='help',
            help='Print usage for the given command.')

    def run(self, args, **kwargs):
        return self.manager.re_emit(args.id)

    @resource.add_auth_token_to_kwargs_from_cli
    def run_and_print(self, args, **kwargs):
        ret = self.run(args, **kwargs)
        if 'message' in ret:
            print(ret['message'])


class TriggerInstanceBranch(resource.ResourceBranch):
    def __init__(self, description, app, subparsers, parent_parser=None):
        super(TriggerInstanceBranch, self).__init__(
            TriggerInstance, description, app, subparsers,
            parent_parser=parent_parser, read_only=True,
            commands={
                'list': TriggerInstanceListCommand,
                'get': TriggerInstanceGetCommand
            })

        self.commands['re-emit'] = TriggerInstanceResendCommand(self.resource, self.app,
                                                                self.subparsers, add_help=False)


class TriggerInstanceListCommand(resource.ResourceCommand):
    display_attributes = ['id', 'trigger', 'occurrence_time']

    attribute_transform_functions = {
        'occurrence_time': format_isodate
    }

    def __init__(self, resource, *args, **kwargs):
        super(TriggerInstanceListCommand, self).__init__(
            resource, 'list', 'Get the list of the 50 most recent %s.' %
            resource.get_plural_display_name().lower(),
            *args, **kwargs)

        self.group = self.parser.add_argument_group()
        self.parser.add_argument('-n', '--last', type=int, dest='last',
                                 default=50,
                                 help=('List N most recent %s; '
                                       'list all if 0.' %
                                       resource.get_plural_display_name().lower()))

        # Filter options
        self.group.add_argument('--trigger', help='Trigger reference to filter the list.')

        self.parser.add_argument('-tg', '--timestamp-gt', type=str, dest='timestamp_gt',
                                 default=None,
                                 help=('Only return trigger instances with occurrence_time '
                                       'greater than the one provided. '
                                       'Use time in the format 2000-01-01T12:00:00.000Z'))
        self.parser.add_argument('-tl', '--timestamp-lt', type=str, dest='timestamp_lt',
                                 default=None,
                                 help=('Only return trigger instances with timestamp '
                                       'lower than the one provided. '
                                       'Use time in the format 2000-01-01T12:00:00.000Z'))
        # Display options
        self.parser.add_argument('-a', '--attr', nargs='+',
                                 default=self.display_attributes,
                                 help=('List of attributes to include in the '
                                       'output. "all" will return all '
                                       'attributes.'))
        self.parser.add_argument('-w', '--width', nargs='+', type=int,
                                 default=None,
                                 help=('Set the width of columns in output.'))

    @resource.add_auth_token_to_kwargs_from_cli
    def run(self, args, **kwargs):
        # Filtering options
        if args.trigger:
            kwargs['trigger'] = args.trigger
        if args.timestamp_gt:
            kwargs['timestamp_gt'] = args.timestamp_gt
        if args.timestamp_lt:
            kwargs['timestamp_lt'] = args.timestamp_lt

        return self.manager.query(limit=args.last, **kwargs)

    def run_and_print(self, args, **kwargs):
        instances = self.run(args, **kwargs)
        self.print_output(reversed(instances), table.MultiColumnTable,
                          attributes=args.attr, widths=args.width,
                          json=args.json,
                          attribute_transform_functions=self.attribute_transform_functions)


class TriggerInstanceGetCommand(resource.ResourceGetCommand):
    display_attributes = ['all']
    attribute_display_order = ['id', 'trigger', 'occurrence_time', 'payload']

    pk_argument_name = 'id'

    @resource.add_auth_token_to_kwargs_from_cli
    def run(self, args, **kwargs):
        resource_id = getattr(args, self.pk_argument_name, None)
        return self.get_resource_by_id(resource_id, **kwargs)
