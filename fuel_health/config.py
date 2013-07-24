# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack, LLC
# Copyright 2013 Mirantis, Inc.
# All Rights Reserved.
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

import os
import sys

from oslo.config import cfg
import requests

from fuel_health.common import log as logging


LOG = logging.getLogger(__name__)

identity_group = cfg.OptGroup(name='identity',
                              title="Keystone Configuration Options")

IdentityGroup = [
    cfg.StrOpt('catalog_type',
               default='identity',
               help="Catalog type of the Identity service."),
    cfg.BoolOpt('disable_ssl_certificate_validation',
                default=False,
                help="Set to True if using self-signed SSL certificates."),
    cfg.StrOpt('uri',
               default='http://192.168.56.103:5000/v2.0/',
               help="Full URI of the OpenStack Identity API (Keystone), v2"),
    cfg.StrOpt('url',
               default='http://192.168.56.103/',
               help="Dashboard Openstack url, v2"),
    cfg.StrOpt('strategy',
               default='keystone',
               help="Which auth method does the environment use? "
                    "(basic|keystone)"),
    cfg.StrOpt('admin_username',
               default='admin',
               help="Administrative Username to use for"
                    "Keystone API requests."),
    cfg.StrOpt('admin_tenant_name',
               default='admin',
               help="Administrative Tenant name to use for Keystone API "
                    "requests."),
    cfg.StrOpt('admin_password',
               default='user',
               help="API key to use when authenticating as admin.",
               secret=True),
]


def register_identity_opts(conf):
    conf.register_group(identity_group)
    for opt in IdentityGroup:
        conf.register_opt(opt, group='identity')


compute_group = cfg.OptGroup(name='compute',
                             title='Compute Service Options')

ComputeGroup = [
    cfg.BoolOpt('create_image_enabled',
                default=True,
                help="Does the test environment support snapshots?"),
    cfg.IntOpt('build_interval',
               default=10,
               help="Time in seconds between build status checks."),
    cfg.IntOpt('build_timeout',
               default=160,
               help="Timeout in seconds to wait for an instance to build."),
    # cfg.BoolOpt('run_ssh',
    #             default=False,
    #             help="Does the test environment support ssh?"),
    # cfg.StrOpt('ssh_user',
    #            default='root',
    #            help="User name used to authenticate to an instance."),
    cfg.IntOpt('ssh_timeout',
               default=50,
               help="Timeout in seconds to wait for authentication to "
                    "succeed."),
    cfg.IntOpt('ssh_channel_timeout',
               default=20,
               help="Timeout in seconds to wait for output from ssh "
                    "channel."),
    # cfg.IntOpt('ip_version_for_ssh',
    #            default=4,
    #            help="IP version used for SSH connections."),
    cfg.StrOpt('catalog_type',
               default='compute',
               help="Catalog type of the Compute service."),
    cfg.StrOpt('path_to_private_key',
               default='/home/slyopka/.ssh/id_rsa',
               help="Path to a private key file for SSH access to remote "
                    "hosts"),
    cfg.ListOpt('controller_nodes',
                default=['192.168.56.103', ],
                help="IP address of one of the controller nodes"),
    cfg.StrOpt('controller_node_ssh_user',
               default='stack',
               help="ssh user of one of the controller nodes"),
    cfg.StrOpt('controller_node_ssh_password',
               default='user',
               help="ssh user pass of one of the controller nodes"),
    cfg.StrOpt('image_name',
               default="TestVM",
               help="Valid secondary image reference to be used in tests."),
    cfg.IntOpt('flavor_ref',
               default=1,
               help="Valid primary flavor to use in tests."),
]


def register_compute_opts(conf):
    conf.register_group(compute_group)
    for opt in ComputeGroup:
        conf.register_opt(opt, group='compute')

image_group = cfg.OptGroup(name='image',
                           title="Image Service Options")

ImageGroup = [
    cfg.StrOpt('api_version',
               default='1',
               help="Version of the API"),
    cfg.StrOpt('catalog_type',
               default='image',
               help='Catalog type of the Image service.'),
]


def register_image_opts(conf):
    conf.register_group(image_group)
    for opt in ImageGroup:
        conf.register_opt(opt, group='image')


network_group = cfg.OptGroup(name='network',
                             title='Network Service Options')

NetworkGroup = [
    cfg.StrOpt('catalog_type',
               default='network',
               help='Catalog type of the Network service.'),
    cfg.StrOpt('tenant_network_cidr',
               default="10.13.0.0/16",
               help="The cidr block to allocate tenant networks from"),
    cfg.BoolOpt('tenant_networks_reachable',
                default=True,
                help="Whether tenant network connectivity should be "
                     "evaluated directly"),
    cfg.BoolOpt('neutron_available',
                default=False,
                help="Whether or not neutron is expected to be available"),
]


def register_network_opts(conf):
    conf.register_group(network_group)
    for opt in NetworkGroup:
        conf.register_opt(opt, group='network')

volume_group = cfg.OptGroup(name='volume',
                            title='Block Storage Options')

VolumeGroup = [
    cfg.IntOpt('build_interval',
               default=10,
               help='Time in seconds between volume availability checks.'),
    cfg.IntOpt('build_timeout',
               default=180,
               help='Timeout in seconds to wait for a volume to become'
                    'available.'),
    cfg.StrOpt('catalog_type',
               default='volume',
               help="Catalog type of the Volume Service"),
]


def register_volume_opts(conf):
    conf.register_group(volume_group)
    for opt in VolumeGroup:
        conf.register_opt(opt, group='volume')


def process_singleton(cls):
    """Wrapper for classes... To be instantiated only one time per process"""
    instances = {}

    def wrapper(*args, **kwargs):
        LOG.info('INSTANCE %s' % instances)
        pid = os.getpid()
        if pid not in instances:
            instances[pid] = cls(*args, **kwargs)
        return instances[pid]

    return wrapper


@process_singleton
class FileConfig(object):
    """Provides OpenStack configuration information."""

    DEFAULT_CONFIG_DIR = os.path.join(os.path.abspath(
        os.path.dirname(__file__)), 'etc')

    DEFAULT_CONFIG_FILE = "test.conf"

    def __init__(self):
        """Initialize a configuration from a conf directory and conf file."""
        config_files = []

        failsafe_path = "/etc/fuel/" + self.DEFAULT_CONFIG_FILE

        # Environment variables override defaults...
        custom_config = os.environ.get('CUSTOM_FUEL_CONFIG')
        LOG.info('CUSTOM CONFIG PATH %s' % custom_config)
        if custom_config:
            path = custom_config
        else:
            conf_dir = os.environ.get('FUEL_CONFIG_DIR',
                                      self.DEFAULT_CONFIG_DIR)
            conf_file = os.environ.get('FUEL_CONFIG', self.DEFAULT_CONFIG_FILE)

            path = os.path.join(conf_dir, conf_file)

            if not (os.path.isfile(path) or
                    'FUEL_CONFIG_DIR' in os.environ or
                    'FUEL_CONFIG' in os.environ):
                path = failsafe_path

        LOG.info("Using fuel config file %s" % path)

        if not os.path.exists(path):
            msg = "Config file %(path)s not found" % locals()
            print >> sys.stderr
        else:
            config_files.append(path)

        cfg.CONF([], project='fuel', default_config_files=config_files)

        register_compute_opts(cfg.CONF)
        register_identity_opts(cfg.CONF)
        register_network_opts(cfg.CONF)
        register_volume_opts(cfg.CONF)
        self.compute = cfg.CONF.compute
        self.identity = cfg.CONF.identity
        self.network = cfg.CONF.network
        self.volume = cfg.CONF.volume
        os.environ['http_proxy'] = 'http://{0}:{1}'.format(
            self.compute.controller_nodes[0], 8888)


class ConfigGroup(object):
  # USE SLOTS

    def __init__(self, opts):
        self.parse_opts(opts)

    def parse_opts(self, opts):
        for opt in opts:
            name = opt.name
            self.__dict__[name] = opt.default

    def __setattr__(self, key, value):
        self.__dict__[key] = value

    def __getitem__(self, key):
        return self.__dict__[key]

    def __setitem(self, key, value):
        self.__dict__[key] = value

    def __repr__(self):
        return u"{0} WITH {1}".format(
            self.__class__.__name__,
            self.__dict__)


@process_singleton
class NailgunConfig(object):

    identity = ConfigGroup(IdentityGroup)
    compute = ConfigGroup(ComputeGroup)
    image = ConfigGroup(ImageGroup)
    network = ConfigGroup(NetworkGroup)
    volume = ConfigGroup(VolumeGroup)

    def __init__(self, parse=True):
        LOG.info('INITIALIZING NAILGUN CONFIG')
        self.nailgun_host = os.environ.get('NAILGUN_HOST', None)
        self.nailgun_port = os.environ.get('NAILGUN_PORT', None)
        self.nailgun_url = 'http://{0}:{1}'.format(self.nailgun_host,
                                                   self.nailgun_port)
        self.cluster_id = os.environ.get('CLUSTER_ID', None)
        self.req_session = requests.Session()
        self.req_session.trust_env = False
        if parse:
            self.prepare_config()

    def prepare_config(self, *args, **kwargs):
        try:
            self._parse_meta()
            self._parse_cluster_attributes()
            self._parse_nodes_cluster_id()
            self._parse_networks_configuration()
            self.set_endpoints()
            self.set_proxy()
        except Exception, e:
            LOG.warning('Nailgun config creation failed. '
                        'Something wrong with endpoints')

    def _parse_cluster_attributes(self):
        api_url = '/api/clusters/%s/attributes' % self.cluster_id
        response = self.req_session.get(self.nailgun_url+api_url)
        LOG.info('RESPONSE %s STATUS %s' % (api_url, response.status_code))
        data = response.json()
        LOG.info('RESPONSE FROM %s - %s' % (api_url, data))
        access_data = data['editable']['access']
        self.identity.admin_tenant_name = access_data['tenant']['value']
        self.identity.admin_username = access_data['user']['value']
        self.identity.admin_password = access_data['password']['value']

    def _parse_nodes_cluster_id(self):
        api_url = '/api/nodes?clusters_id=%s' % self.cluster_id
        response = self.req_session.get(self.nailgun_url+api_url)
        LOG.info('RESPONSE %s STATUS %s' % (api_url, response.status_code))
        data = response.json()
        controller_nodes = filter(lambda node: node['role'] == 'controller',
                                  data)
        controller_ips = []
        conntroller_names = []
        public_ips = []
        for node in controller_nodes:
            public_network = next(network for network in node['network_data']
                                  if network['name'] == 'public')
            ip = public_network['ip'].split('/')[0]
            public_ips.append(ip)
            controller_ips.append(node['ip'])
            conntroller_names.append(node['fqdn'])
        LOG.info("NAMES %s IPS %s" % (controller_ips, conntroller_names))
        self.compute.public_ips = public_ips
        self.compute.controller_nodes = controller_ips
        self.compute.controller_nodes_name = conntroller_names

    def _parse_meta(self):
        api_url = '/api/clusters/%s' % self.cluster_id
        data = self.req_session.get(self.nailgun_url+api_url).json()
        self.mode = data['mode']

    def _parse_networks_configuration(self):
        api_url = '/api/clusters/%s/network_configuration/' % self.cluster_id
        data = self.req_session.get(self.nailgun_url+api_url).json()
        self.network.raw_data = data

    def _parse_ostf_api(self):
        """
            will leave this
        """
        api_url = '/api/ostf/%s' % self.cluster_id
        response = self.req_session.get(self.nailgun_url+api_url)
        data = response.json()
        self.identity.url = data['horizon_url'] + 'dashboard'
        self.identity.uri = data['keystone_url'] + 'v2.0/'

    def set_proxy(self):
        """Sets environment property for http_proxy:
            To behave properly - method must be called after all nailgun params
            is processed
        """
        os.environ['http_proxy'] = 'http://{0}:{1}'.format(
            self.compute.controller_nodes[0], 8888)

    def set_endpoints(self):
        public_vip = self.network.raw_data.get('public_vip', None)
        # workaround for api without public_vip for ha mode
        if not public_vip and self.mode == 'ha':
            self._parse_ostf_api()
        else:
            endpoint = public_vip or self.compute.public_ips[0]
            self.identity.url = 'http://{0}/{1}/'.format(endpoint, 'dashboard')
            self.identity.uri = 'http://{0}:{1}/{2}/'.format(
                endpoint, 5000, 'v2.0')


def FuelConfig():
    # if all(item in os.environ for item in (
    #     'NAILGUN_HOST', 'NAILGUN_PORT', 'CLUSTER_ID')):
    return NailgunConfig()
