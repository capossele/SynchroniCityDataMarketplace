# -*- coding: utf-8 -*-

# Copyright (c) 2018, Digital Catapult

# This file belongs to the orion context broker plugin
# of the Business API Ecosystem.

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Author: Angelo Capossele

from __future__ import unicode_literals

import requests
from requests.exceptions import HTTPError
from urlparse import parse_qs, urlparse
from urllib import quote_plus

from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.conf import settings

from wstore.asset_manager.resource_plugins.plugin import Plugin
from wstore.asset_manager.resource_plugins.plugin_error import PluginError
from wstore.store_commons.errors import ConflictError

from .config import *
from .keystone_client import KeystoneClient
import json

class OrionPlugin(Plugin):

    def _pack_json_role(self, name, application_id):
        data = json.dumps({'role' : {
                            'name' : name, 
                            'application_id' : application_id}})
        return json.loads(data)

    def _get_user_id(self, keystone_client, domain_id, username):
        # Get provider and seller role ids
        users = keystone_client.get_user_by_username(username)
        user_info = [user for user in users['users'] if user['domain_id'] == domain_id]

        if not len(user_info):
            raise PluginError('Your user is not registered in the underlying Keystone instance')

        return user_info[0]['id']

    def on_post_product_spec_validation(self, provider, asset):
        # Extract related information from the asset
        parsed_url = urlparse(asset.download_link)
        
        service = "" 
        if 'service' in asset.meta_info:
            service = asset.meta_info['service']

        try:
            # Log the plugin in the Keystone instance
            keystone_client = KeystoneClient(KEYSTONE_USER, KEYSTONE_PWD, ADMIN_DOMAIN, KEYSTONE_PROTOCOL, KEYSTONE_HOST, KEYSTONE_PORT)

            # Check that provided application exists
            application_info = keystone_client.get_application_by_id(asset.meta_info['application_id'])

            if not len(application_info['consumer']):
                raise ObjectDoesNotExist('The Application ' + asset.meta_info['application_id'] + ' could not be found')

            application_id = asset.meta_info['application_id']
            
            domain_id = keystone_client.get_domain_id(ADMIN_DOMAIN)
            provider_id = provider.name #self._get_user_id(keystone_client, domain_id, provider.name)
        
            #provider_role_name = service + ":provider"
            provider_role_name = "data_provider"
            provider_role_id = keystone_client.get_role_id_by_name(application_id, provider_role_name)
        except HTTPError:
            raise PluginError('It has not been possible to connect with Keystone')
        
        try:
            # Validate provider permissions
            if not provider_role_id:
                raise PermissionDenied('You are not authorized to create offerings for the specified Application')
            if not keystone_client.check_role(application_id, provider_id, provider_role_id):
                raise PermissionDenied('You are not authorized to create offerings for the specified Application')
        except HTTPError as e:
            # The role assignment does not exist; thus the user is not authorized
            if e.response.status_code == 404:
                raise PermissionDenied('You are not authorized to create offerings for the specified Application')
            else:
                raise PluginError('It has not been possible to connect with Keystone')
        
        #create authroization role for the asset
        try:
            s = parsed_url.path
            parsed_query = parse_qs(parsed_url.query, keep_blank_values=True)
            resource = ""
            resource_type = ""
            attr = ""
            
            if (s.find('/v2/entities') == -1):
                raise PluginError("URL not valid")

            if 'type' in parsed_query:
                resource_type = parsed_query['type'][0]
            
            if 'id' in parsed_query:
                resource = parsed_query['id'][0]

            #role_name = service + ':' + resource
            role_name = service + '|' + 'GET' + '|' + resource_type  + '|' + resource + '|' + attr
            json_role = self._pack_json_role(role_name, application_id)
            if not (keystone_client.get_role_id_by_name(application_id, role_name)):
                role = keystone_client.create_role(json_role)

        except HTTPError as e:
            raise PluginError(e)
         
        # Save related metadata to avoid future requests
        asset.meta_info['role'] = role_name
        asset.meta_info['service'] = service
        asset.meta_info['domain_id'] = domain_id
        asset.meta_info['application_id'] = application_id
        
        asset.save()

    #def on_post_product_offering_validation(self, asset, product_offering):
        # Parse the pricing models to check usage models
        # provided_usage = [price_model['unitsOfMeasure']
        #                   for price_model in product_offering['productOfferingPrice']
        #                   if price_model['priceType'].lower() == 'usage'] if 'productOfferingPrice' in product_offering else []

        # if provided_usage:
        #     # Get the valid models
        #     parsed_url = urlparse(asset.get_url())
        #     units_service = parsed_url.scheme + '://' + parsed_url.netloc + '/accounting/units'

        #     resp = requests.get(units_service)
        #     valid_units = resp.json()

        #     # Check that all usage models are supported
        #     for model in provided_usage:
        #         if model not in valid_units['units']:
        #             raise PluginError('The usage model ' + model + ' is not supported by the accounting service')

    #def _notify_accounting(self, asset, order, contract, type_):
        # parsed_url = urlparse(asset.download_link)
        # notification = {
        #     'orderId': unicode(order.order_id),
        #     'productId': unicode(contract.product_id),
        # }

        # if type_ == 'add':
        #     notification['customer'] = order.customer.username
        #     notification['acquisition'] = {
        #         'roleId': asset.meta_info['role_id'],
        #         'domain': asset.meta_info['tenant'],
        #         'servicePath': asset.meta_info['service'],
        #         'unit': [price_model['unit'] for price_model in contract.pricing_model['pay_per_use']][0]
        #     }

        # url = parsed_url.scheme + '://' + parsed_url.netloc + '/accounting/acquisitions/' + type_

        # resp = requests.post(url, json=notification)
        # if resp.status_code != 201:
        #     raise PluginError('Error notifying the product acquisition to the accounting server')

    def on_product_acquisition(self, asset, contract, order):
        # Extract related information from the asset
        #parsed_url = urlparse(asset.download_link)

        try:
            keystone_client = KeystoneClient(KEYSTONE_USER, KEYSTONE_PWD, ADMIN_DOMAIN, KEYSTONE_PROTOCOL, KEYSTONE_HOST, KEYSTONE_PORT)

            
            # Check the customer user
            customer_id = order.owner_organization.name#self._get_user_id(keystone_client, asset.meta_info['domain_id'], order.owner_organization.name)

            role_id = keystone_client.get_role_id_by_name(asset.meta_info['application_id'], asset.meta_info['role'])
            if role_id:
                # Give the user the new role
                keystone_client.grant_role(asset.meta_info['application_id'], customer_id, role_id)
            else:
                raise PluginError('It has not been possible to use this role: ' + asset.meta_info['role'] + ' with Keystone')

        except HTTPError as e:
            if e.response.status_code == 409:
                raise ConflictError('You already own the offered role')
            else:
                raise PluginError('It has not been possible to connect with Keystone')

        
        
        
        # # If the model is usage, send usage notification
        # if 'pay_per_use' in contract.pricing_model:
        #     self._notify_accounting(asset, order, contract, 'add')

    #def on_product_suspension(self, asset, contract, order):
        # parsed_url = urlparse(asset.download_link)

        # try:
        #     keystone_client = KeystoneClient(KEYSTONE_USER, KEYSTONE_PWD, ADMIN_DOMAIN, parsed_url.scheme, parsed_url.hostname)

        #     # Check the customer user
        #     customer_id = self._get_user_id(keystone_client, asset.meta_info['domain_id'], order.owner_organization.name)

        #     # Remove the role from the user
        #     keystone_client.revoke_role(asset.meta_info['project_id'], customer_id, asset.meta_info['role_id'])

        # except HTTPError:
        #     raise PluginError('It has not been possible to connect with Keystone')

        # # If the model is usage, send usage notification
        # if 'pay_per_use' in contract.pricing_model:
        #     self._notify_accounting(asset, order, contract, 'remove')