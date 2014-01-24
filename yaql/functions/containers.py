#    Copyright (c) 2014 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import collections
import types
from yaql.language.exceptions import YaqlExecutionException

from yaql.language.engine import parameter
from yaql.language.utils import limit


@parameter("index", arg_type=types.IntType)
def get_by_index(data, index):
    if isinstance(data, types.GeneratorType):
        data = list(data)
    return data[index]


@parameter("self", arg_type=collections.Iterable,
           custom_validator=lambda v: not isinstance(v, types.StringTypes))
@parameter("predicate", function_only=True, lazy=True)
def filter_by_predicate(self, predicate):
    for item in self:
        r = predicate(item)
        if not isinstance(r, types.BooleanType):
            raise YaqlExecutionException("Not a predicate")
        if r is True:
            yield item


def build_list(*args):
    res = []
    for arg in args:
        if isinstance(arg, types.GeneratorType):
            arg = limit(arg)
        res.append(arg)
    return res


@parameter("b", arg_type=collections.Iterable,
           custom_validator=lambda v: not isinstance(v, types.StringTypes))
def is_in(a, b):
    return a in b


@parameter('self', arg_type=collections.Iterable,
           custom_validator=lambda v: not isinstance(v, types.DictionaryType))
@parameter('att_name', constant_only=True)
def collection_attribution(self, att_name):
    def get_att_or_key(col_item):
        value = att_name
        if isinstance(col_item, types.DictionaryType):
            return col_item.get(value)
        else:
            return getattr(col_item, value)

    for item in self:
        val = get_att_or_key(item)
        yield val


@parameter('arg1', lazy=True,
           custom_validator=lambda v: v.key != 'operator_=>')
def build_new_tuple(arg1, arg2):
    return arg1(), arg2


@parameter('arg1', lazy=True,
           custom_validator=lambda v: v.key == 'operator_=>')
def append_tuple(arg1, arg2):
    res = []
    for tup in arg1():
        res.append(tup)
    res.append(arg2)
    return tuple(res)


def build_dict(*tuples):
    try:
        return {key: value for key, value in tuples}
    except ValueError as e:
        raise YaqlExecutionException("Not a valid dictionary", e)


def add_to_context(context):
    context.register_function(get_by_index, 'where')
    context.register_function(filter_by_predicate, 'where')
    context.register_function(build_list, 'list')
    context.register_function(build_dict, 'dict')
    context.register_function(is_in, 'operator_in')
    context.register_function(collection_attribution, 'operator_.')
    context.register_function(build_new_tuple, 'operator_=>')
    context.register_function(append_tuple, 'operator_=>')