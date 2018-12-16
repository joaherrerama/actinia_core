# -*- coding: utf-8 -*-
#######
# actinia-core - an open source REST API for scalable, distributed, high
# performance processing of geographical data that uses GRASS GIS for
# computational tasks. For details, see https://actinia.mundialis.de/
#
# Copyright (c) 2016-2018 Sören Gebbert and mundialis GmbH & Co. KG
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
#######

"""
Raster layer resources
"""
from flask import jsonify, make_response
from copy import deepcopy
from flask_restful_swagger_2 import swagger, Schema
import pickle
from .ephemeral_processing import EphemeralProcessing
from .persistent_processing import PersistentProcessing
from .common.redis_interface import enqueue_job
from .common.response_models import ProcessingResponseModel, ProcessingErrorResponseModel
from .common.exceptions import AsyncProcessError
from .map_layer_base import MapLayerRegionResourceBase, SetRegionModel

__license__ = "GPLv3"
__author__ = "Sören Gebbert"
__copyright__ = "Copyright 2016-2018, Sören Gebbert and mundialis GmbH & Co. KG"
__maintainer__ = "Sören Gebbert"
__email__ = "soerengebbert@googlemail.com"


class RasterInfoModel(Schema):
    """Schema that contains raster map layer information
    """
    type = 'object'
    properties = {
        'cells': {'type': 'string'},
        'cols': {'type': 'string'},
        'comments': {'type': 'string'},
        'creator': {'type': 'string'},
        'database': {'type': 'string'},
        'datatype': {'type': 'string'},
        'maptype': {'type': 'string'},
        'east': {'type': 'string'},
        'date': {'type': 'string'},
        'description': {'type': 'string'},
        'ewres': {'type': 'string'},
        'max': {'type': 'string'},
        'min': {'type': 'string'},
        'ncats': {'type': 'string'},
        'nsres': {'type': 'string'},
        'location': {'type': 'string'},
        'map': {'type': 'string'},
        'mapset': {'type': 'string'},
        'rows': {'type': 'string'},
        'source1': {'type': 'string'},
        'north': {'type': 'string'},
        'source2': {'type': 'string'},
        'units': {'type': 'string'},
        'vdatum': {'type': 'string'},
        'south': {'type': 'string'},
        'timestamp': {'type': 'string'},
        'title': {'type': 'string'},
        'west': {'type': 'string'}
    }
    example = {
        "cells": "2025000",
        "cols": "1500",
        "comments": "\"r.proj input=\"ned03arcsec\" location=\"northcarolina_latlong\" mapset=\"\\helena\" output=\"elev_ned10m\" method=\"cubic\" resolution=10\"",
        "creator": "\"helena\"",
        "database": "/tmp/gisdbase_75bc0828",
        "datatype": "FCELL",
        "date": "\"Tue Nov  7 01:09:51 2006\"",
        "description": "\"generated by r.proj\"",
        "east": "645000",
        "ewres": "10",
        "location": "nc_spm_08",
        "map": "elevation",
        "mapset": "PERMANENT",
        "max": "156.3299",
        "min": "55.57879",
        "ncats": "255",
        "north": "228500",
        "nsres": "10",
        "rows": "1350",
        "source1": "\"\"",
        "source2": "\"\"",
        "south": "215000",
        "timestamp": "\"none\"",
        "title": "\"South-West Wake county: Elevation NED 10m\"",
        "units": "\"none\"",
        "vdatum": "\"none\"",
        "west": "630000"
    }


class RasterInfoResponseModel(ProcessingResponseModel):
    """Response schema for raster map layer information.
    """
    type = 'object'
    properties = deepcopy(ProcessingResponseModel.properties)
    properties["process_results"] = RasterInfoModel
    required = deepcopy(ProcessingResponseModel.required)
    # required.append("process_results")
    example = {
        "accept_datetime": "2018-05-02 10:44:11.764375",
        "accept_timestamp": 1525257851.7643716,
        "api_info": {
            "endpoint": "rasterlayerresource",
            "method": "GET",
            "path": "/locations/nc_spm_08/mapsets/PERMANENT/raster_layers/elevation",
            "request_url": "http://localhost:8080/locations/nc_spm_08/mapsets/PERMANENT/raster_layers/elevation"
        },
        "datetime": "2018-05-02 10:44:11.897704",
        "http_code": 200,
        "message": "Processing successfully finished",
        "process_chain_list": [
            {
                "1": {
                    "flags": "gre",
                    "inputs": {
                        "map": "elevation@PERMANENT"
                    },
                    "module": "r.info"
                }
            }
        ],
        "process_log": [
            {
                "executable": "r.info",
                "parameter": [
                    "map=elevation@PERMANENT",
                    "-gre"
                ],
                "return_code": 0,
                "run_time": 0.050168514251708984,
                "stderr": [
                    ""
                ],
                "stdout": "..."}
        ],
        "process_results": {
            "cells": "2025000",
            "cols": "1500",
            "comments": "\"r.proj input=\"ned03arcsec\" location=\"northcarolina_latlong\" mapset=\"\\helena\" output=\"elev_ned10m\" method=\"cubic\" resolution=10\"",
            "creator": "\"helena\"",
            "database": "/actinia/workspace/temp_db/gisdbase_5f1a5262c8bf4d4789348ffa2406ec3e",
            "datatype": "FCELL",
            "date": "\"Tue Nov  7 01:09:51 2006\"",
            "description": "\"generated by r.proj\"",
            "east": "645000",
            "ewres": "10",
            "location": "nc_spm_08",
            "map": "elevation",
            "mapset": "PERMANENT",
            "max": "156.3299",
            "min": "55.57879",
            "ncats": "255",
            "north": "228500",
            "nsres": "10",
            "rows": "1350",
            "source1": "\"\"",
            "source2": "\"\"",
            "south": "215000",
            "timestamp": "\"none\"",
            "title": "\"South-West Wake county: Elevation NED 10m\"",
            "units": "\"none\"",
            "vdatum": "\"none\"",
            "west": "630000"
        },
        "progress": {
            "num_of_steps": 1,
            "step": 1
        },
        "resource_id": "resource_id-0a3d6b2b-0962-4d01-8993-7997f15d1595",
        "status": "finished",
        "time_delta": 0.13338971138000488,
        "timestamp": 1525257851.8976946,
        "urls": {
            "resources": [],
            "status": "http://localhost:8080/resources/user/resource_id-0a3d6b2b-0962-4d01-8993-7997f15d1595"
        },
        "user_id": "user"
    }


class RasterRegionCreationModel(Schema):
    """Schema for random raster map layer generation using r.mapcalc in a specific region
    """
    type = 'object'
    properties = {
        'region': SetRegionModel,
        'expression': {
            'type': 'string',
            'description': 'The r.mapcalc expression to create a new raster map layer. '
                           'The expression must not contain the name of the new raster map layer '
                           'only the statement after the equal operator: "a + b" instead of "c = a + b"',
            'default': "1"
        }
    }


class RasterLayerResource(MapLayerRegionResourceBase):
    """Return information about a specific raster layer as JSON
    """

    @swagger.doc({
        'tags': ['Raster Management'],
        'description': 'Get information about an existing raster map layer. Minimum required user role: user.',
        'parameters': [
            {
                'name': 'location_name',
                'description': 'The location name',
                'required': True,
                'in': 'path',
                'type': 'string',
                'default': 'nc_spm_08'
            },
            {
                'name': 'mapset_name',
                'description': 'The name of the mapset that contains the required raster map layer',
                'required': True,
                'in': 'path',
                'type': 'string',
                'default': 'PERMANENT'
            },
            {
                'name': 'raster_name',
                'description': 'The name of the raster map layer to get information about',
                'required': True,
                'in': 'path',
                'type': 'string',
                'default': 'elevation'
            }
        ],
        'consumes': ['application/json'],
        'produces': ["application/json"],
        'responses': {
            '200': {
                'description': 'The raster map layer information',
                'schema': RasterInfoResponseModel
            },
            '400': {
                'description': 'The error message and a detailed log why gathering raster map '
                               'layer information did not succeeded',
                'schema': ProcessingErrorResponseModel
            }
        }
    })
    def get(self, location_name, mapset_name, raster_name):
        """Get information about an existing raster map layer.
        """
        rdc = self.preprocess(has_json=False, has_xml=False,
                              location_name=location_name,
                              mapset_name=mapset_name,
                              map_name=raster_name)
        if rdc:
            enqueue_job(self.job_timeout, start_info_job, rdc)
            http_code, response_model = self.wait_until_finish(0.02)
        else:
            http_code, response_model = pickle.loads(self.response_data)

        return make_response(jsonify(response_model), http_code)

    @swagger.doc({
        'tags': ['Raster Management'],
        'description': 'Delete an existing raster map layer. Minimum required user role: user.',
        'parameters': [
            {
                'name': 'location_name',
                'description': 'The location name',
                'required': True,
                'in': 'path',
                'type': 'string'
            },
            {
                'name': 'mapset_name',
                'description': 'The name of the mapset that contains the required raster map layer',
                'required': True,
                'in': 'path',
                'type': 'string'
            },
            {
                'name': 'raster_name',
                'description': 'The name of the raster map layer to be deleted',
                'required': True,
                'in': 'path',
                'type': 'string'
            }
        ],
        'produces': ["application/json"],
        'responses': {
            '200': {
                'description': 'Successfuly delete a raster map layer',
                'schema': ProcessingResponseModel
            },
            '400': {
                'description': 'The error message and a detailed log why raster map '
                               'layer deletion did not succeeded',
                'schema': ProcessingErrorResponseModel
            }
        }
    })
    def delete(self, location_name, mapset_name, raster_name):
        """Delete an existing raster map layer.
        """
        rdc = self.preprocess(has_json=False, has_xml=False,
                              location_name=location_name,
                              mapset_name=mapset_name,
                              map_name=raster_name)
        if rdc:
            enqueue_job(self.job_timeout, start_delete_job, rdc)
            http_code, response_model = self.wait_until_finish(0.1)
        else:
            http_code, response_model = pickle.loads(self.response_data)

        return make_response(jsonify(response_model), http_code)

    @swagger.doc({
        'tags': ['Raster Management'],
        'description': 'Create a new raster map layer based on a r.mapcalc expression '
                       'in a user specific region. This method will fail if the map already exists. '
                       'Minimum required user role: user.',
        'parameters': [
            {
                'name': 'location_name',
                'description': 'The location name',
                'required': True,
                'in': 'path',
                'type': 'string'
            },
            {
                'name': 'mapset_name',
                'description': 'The name of the mapset in which the raster map layer should be created',
                'required': True,
                'in': 'path',
                'type': 'string'
            },
            {
                'name': 'raster_name',
                'description': 'The name of the new raster map layer to be created',
                'required': True,
                'in': 'path',
                'type': 'string'
            },
            {
                'name': 'creation_params',
                'description': 'Parameters to create raster map layer '
                               'using r.mapcalc in a specific region.',
                'required': True,
                'in': 'body',
                'schema': RasterRegionCreationModel
            }
        ],
        'consumes': ['application/json'],
        'produces': ["application/json"],
        'responses': {
            '200': {
                'description': 'Raster map layer creation information',
                'schema': ProcessingResponseModel
            },
            '400': {
                'description': 'The error message and a detailed log why raster map '
                               'layer creation did not succeeded',
                'schema': ProcessingErrorResponseModel
            }
        }
    })
    def post(self, location_name, mapset_name, raster_name):
        """Create a new raster layer using r.mapcalc expression in a specific region and value
        """
        rdc = self.preprocess(has_json=True, has_xml=False,
                              location_name=location_name,
                              mapset_name=mapset_name,
                              map_name=raster_name)
        if rdc:
            enqueue_job(self.job_timeout, start_create_job, rdc)
            http_code, response_model = self.wait_until_finish(0.1)
        else:
            http_code, response_model = pickle.loads(self.response_data)

        return make_response(jsonify(response_model), http_code)


def start_info_job(*args):
    processing = EphemeralRasterInfo(*args)
    processing.run()


class EphemeralRasterInfo(EphemeralProcessing):

    def __init__(self, *args):

        EphemeralProcessing.__init__(self, *args)

    def _execute(self):
        """Read info from a raster layer

        Use a temporary mapset for processing
        """
        self._setup()

        raster_name = self.map_name
        self.required_mapsets.append(self.mapset_name)

        pc = {}
        pc["1"] = {"module": "r.info", "inputs": {"map": raster_name + "@" + self.mapset_name},
                   "flags": "gre"}

        self.skip_region_check = True
        process_list = self._create_temporary_grass_environment_and_process_list(process_chain=pc,
                                                                                 skip_permission_check=True)
        self._execute_process_list(process_list)

        kv_list = self.module_output_log[0]["stdout"].split("\n")

        raster_info = {}

        for string in kv_list:
            if "=" in string:
                k, v = string.split("=", 1)
                raster_info[k] = v

        self.module_results = RasterInfoModel(**raster_info)


def start_delete_job(*args):
    processing = PersistentRasterDeleter(*args)
    processing.run()


class PersistentRasterDeleter(PersistentProcessing):

    def __init__(self, *args):
        PersistentProcessing.__init__(self, *args)

    def _execute(self):
        """Delete a specific raster layer

        Use the original mapset for processing
        """
        self._setup()

        raster_name = self.map_name
        self.required_mapsets.append(self.target_mapset_name)

        pc = {}
        pc["1"] = {"module": "g.remove", "inputs": {"type": "raster",
                                                    "name": raster_name},
                   "flags": "f"}

        self.skip_region_check = True
        process_list = self._validate_process_chain(process_chain=pc,
                                                    skip_permission_check=True)
        self._check_lock_target_mapset()
        self._create_temp_database(self.required_mapsets)
        self._create_grass_environment(grass_data_base=self.temp_grass_data_base,
                                       mapset_name=self.target_mapset_name)

        self._execute_process_list(process_list)

        if "WARNING: No data base element files found" in "\n".join(self.module_output_log[0]["stderr"]):
            raise AsyncProcessError("Raster layer <%s> not found" % raster_name)

        self.finish_message = "Raster layer <%s> successfully removed." % raster_name


def start_create_job(*args):
    processing = PersistentRasterCreator(*args)
    processing.run()


class PersistentRasterCreator(PersistentProcessing):

    def __init__(self, *args):

        PersistentProcessing.__init__(self, *args)

    def _execute(self):
        """Create a specific raster layer

        This approach is complex, since the raster generation is performed in a local
        temporary mapset that is later merged into the target mapset. Workflow:

        1. Check the process chain
        2. Lock the temp and target mapsets
        3. Setup GRASS and create the temporary mapset
        4. Execute g.list of the first process chain to check if the target raster exists
        5. If the target raster does not exists then run r.mapcalc
        6. Copy the local temporary mapset to the storage and merge it into the target mapset
        """
        self._setup()

        region = None
        if "region" in self.request_data:
            region = self.request_data["region"]
        expression = self.request_data["expression"]
        raster_name = self.map_name
        self.required_mapsets.append(self.target_mapset_name)

        pc_1 = {}
        pc_1["1"] = {"module": "g.list", "inputs": {"type": "raster",
                                                    "pattern": raster_name,
                                                    "mapset": self.target_mapset_name}}
        # Check the first process chain
        pc_1 = self._validate_process_chain(skip_permission_check=True,
                                            process_chain=pc_1)

        pc_2 = {}
        if region:
            pc_2["1"] = {"module": "g.region", "inputs": {}, "flags": "g"}
            for key in region:
                value = region[key]
                pc_2["1"]["inputs"][key] = value

        pc_2["2"] = {"module": "r.mapcalc", "inputs": {"expression": "%s = %s" % (raster_name,
                                                                                  expression)}}
        # Check the second process chain
        pc_2 = self._validate_process_chain(skip_permission_check=True,
                                            process_chain=pc_2)

        self._check_lock_target_mapset()
        self._lock_temp_mapset()
        self._create_temporary_grass_environment()
        self._execute_process_list(pc_1)

        # check if raster exists
        raster_list = self.module_output_log[0]["stdout"].split("\n")

        if len(raster_list[0]) > 0:
            raise AsyncProcessError("Raster layer <%s> exists." % raster_name)

        self._execute_process_list(pc_2)
        self._copy_merge_tmp_mapset_to_target_mapset()

        self.finish_message = "Raster layer <%s> successfully created." % raster_name
