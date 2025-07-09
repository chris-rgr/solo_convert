from dataclasses import dataclass
from typing import List, Optional, Union
import os

@dataclass(frozen=True)
class MetricBase:
    """
    Metric base class
    """

    id: str
    sensor_id: str
    sequence: int
    annotation_id: str
    description: str

    TYPE_GENERIC = "type.unity.com/unity.solo.GenericMetric"
    TYPE_OBJECT_COUNT = "type.unity.com/unity.solo.ObjectCountMetric"
    TYPE_OCCLUSION = "type.unity.com/unity.solo.OcclusionMetric"


@dataclass(frozen=True)
class ObjectCountValue:
    """
    Represents a single label count in ObjectCountMetric
    """
    label_id: int
    label_name: str
    count: int

    @staticmethod
    def from_dict(_dict: dict) -> 'ObjectCountValue':
        return ObjectCountValue(
            label_id=_dict['labelId'],
            label_name=_dict['labelName'],
            count=_dict['count']
        )

@dataclass(frozen=True)
class OcclusionValue:
    """
    Represents visibility metrics for a single instance in OcclusionMetric
    """
    instance_id: int
    percent_visible: float
    percent_in_frame: float
    visibility_in_frame: float

    @staticmethod
    def from_dict(_dict: dict) -> 'OcclusionValue':
        return OcclusionValue(
            instance_id=_dict['instanceId'],
            percent_visible=_dict['percentVisible'],
            percent_in_frame=_dict['percentInFrame'],
            visibility_in_frame=_dict['visibilityInFrame']
        )

@dataclass(frozen=True)
class GenericMetric(MetricBase):
    """
    Represents a generic metric with a single value
    """

    type_name = "type.unity.com/unity.solo.GenericMetric"

    value: Union[int, float, str]

    @staticmethod
    def from_dict(_dict: dict) -> 'GenericMetric':
        return GenericMetric(
            id=_dict['id'],
            sequence = int(_dict['path'].split('.')[-1]),
            sensor_id=_dict['sensorId'],
            annotation_id=_dict['annotationId'],
            description=_dict['description'],
            value = None if 'value' not in _dict else _dict['value']
        )

@dataclass(frozen=True)
class ObjectCountMetric(MetricBase):
    """
    Represents an object count metric containing counts for multiple labels
    """

    type_name = "type.unity.com/unity.solo.ObjectCountMetric"

    values: List[ObjectCountValue]

    @staticmethod
    def from_dict(_dict: dict) -> 'ObjectCountMetric':
        return ObjectCountMetric(
            id=_dict['id'],
            sequence = int(_dict['path'].split('.')[-1]),
            sensor_id=_dict['sensorId'],
            annotation_id=_dict['annotationId'],
            description=_dict['description'],
            values = None if 'values' not in _dict else [ObjectCountValue.from_dict(v) for v in _dict['values']]
        )

@dataclass(frozen=True)
class OcclusionMetric(MetricBase):
    """
    Represents visibility metrics for labeled objects
    """
    
    type_name = "type.unity.com/unity.solo.OcclusionMetric"

    values: List[OcclusionValue]

    @staticmethod
    def from_dict(_dict: dict) -> 'OcclusionMetric':
        return OcclusionMetric(
            id = _dict['id'],
            sequence =  int(_dict['path'].split('.')[-1]),
            sensor_id = _dict['sensorId'],
            annotation_id = _dict['annotationId'],
            description = _dict['description'],
            values = None if 'values' not in _dict else [OcclusionValue.from_dict(v) for v in _dict['values']]
        )

@dataclass(frozen=True)
class Metric:
    """
    Represents a single metric of a sequence in UnityData.
    """
    id: str
    sequence: int
    sensor_id: str
    description: str


    generic_metrics: List[GenericMetric]
    object_count_metric: ObjectCountMetric
    occlusion_metric: OcclusionMetric

    @staticmethod
    def from_dict(_dict: dict) -> 'Metric':
        """
        Create a Metric from a dictionary.
        :param _dict:
        :return: A Metric object
        """

        #metrics = {}
        #for metric in _dict:
        #    print(_dict)
        #    metrics[metric["@type"]] = metric
        
        object_count_metric = None if _dict["@type"] != MetricBase.TYPE_OBJECT_COUNT else ObjectCountMetric.from_dict(_dict)
        occlusion_metric = None if _dict["@type"] != MetricBase.TYPE_OCCLUSION else OcclusionMetric.from_dict(_dict)

        return Metric(
            id=_dict['id'],
            sequence = int(_dict['path'].split('.')[-1]),
            sensor_id=_dict['sensorId'],
            description=_dict['description'],
            generic_metrics= None,
            object_count_metric=object_count_metric,
            occlusion_metric=occlusion_metric,
        )


    #@staticmethod
    #def from_dict(_dict: dict) -> Union[GenericMetric, ObjectCountMetric, OcclusionMetric]:
    #    """
    #    Create the appropriate metric type based on the @type field in the dictionary
    #    """
    #    metric_type = _dict['@type']
    #    
    #    if metric_type == MetricBase.TYPE_GENERIC:
    #        result = GenericMetric.from_dict(_dict)
    #        return None if result.value is None else result
    #    elif metric_type == MetricBase.TYPE_OBJECT_COUNT:
    #        result = ObjectCountMetric.from_dict(_dict)
    #        return None if result.values is None or len(result.values) == 0 else result
    #    elif metric_type == MetricBase.TYPE_OCCLUSION:
    #        result = OcclusionMetric.from_dict(_dict)
    #        return None if result.values is None or len(result.values) == 0 else result
    #    else:
    #        raise ValueError(f"Unknown metric type: {metric_type}")