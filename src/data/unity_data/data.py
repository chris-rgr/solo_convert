import glob
import json
from typing import List, Dict

from .capture import Capture
from .label import Label
from .metric import MetricBase
from .metric import Metric
import os


class UnityData:
    """
    UnityData represents a collection of captures from Unity.
    """
    data_path: str
    labels: List[Label]
    captures_by_sequence: Dict[int, List[Capture]]
    metrics_by_sequence: Dict[int, List[MetricBase]]

    def read_labels(self):
        """
        Read labels from annotation_definitions.json.
        """
        with open(f"{self.data_path}/annotation_definitions.json") as f:
            data = json.load(f)
            annotation_definitions = data['annotationDefinitions']

        labels = []
        counter = 0

        for annotation_definition in annotation_definitions:
            if 'spec' not in annotation_definition or not isinstance(annotation_definition['spec'], list) or len(
                    annotation_definition['spec']) == 0:
                continue

            for spec in annotation_definition['spec']:
                if 'label_id' not in spec or 'label_name' not in spec:
                    continue

                # If no label with name exists, create a label
                if not any(label.name == spec['label_name'] for label in labels):
                    labels.append(Label(counter, spec['label_id'], spec['label_name']))
                    counter += 1

        self.labels = labels

    def get_sorted_data_files(self):
        """
        Get all frame_data.json files in the sequences sorted by sequence number.
        :return: List of frame_data.json files
        """
        frame_data_files = glob.glob(os.path.join(self.data_path, '**', '*frame_data.json'), recursive=True)
        frame_data_files.sort(key=lambda x: int(os.path.basename(os.path.dirname(x)).split('.')[-1]))
        return frame_data_files


    def read_captures(self, frame_data_files):
        """
        Read captures from frame_data.json files.
        """
        captures = []
        for file in frame_data_files:
            with open(file) as f:
                data_dict = json.load(f)

                # Continue if data_dict has no key captures or captures is empty or not an array
                if 'captures' not in data_dict or not isinstance(data_dict['captures'], list) or len(
                        data_dict['captures']) == 0:
                    continue

                for capture_path in data_dict['captures']:
                    capture_path['path'] = os.path.dirname(file)
                    captures.append(capture_path)

        # Collect sequences for efficient access
        self.captures_by_sequence = {}   
        for capture_path in captures:
            capture_instance = Capture.from_dict(capture_path, self.labels)

            if capture_instance.sequence not in self.captures_by_sequence:
                self.captures_by_sequence[capture_instance.sequence] = []
            self.captures_by_sequence[capture_instance.sequence].append(capture_instance)

    def read_metrics(self, frame_data_files):
        """
        Read metrics from frame_data.json files.
        """
        metrics = []
        for file in frame_data_files:
            with open(file) as f:
                data_dict = json.load(f)

                # Continue if data_dict has no metrics key or metrics is empty or not an array
                if 'metrics' not in data_dict or not isinstance(data_dict['metrics'], list) or len(
                        data_dict['metrics']) == 0:
                    continue

                for metrics_path in data_dict['metrics']:
                    metrics_path['path'] = os.path.dirname(file)
                    metrics.append(metrics_path)

        # Collect sequences for efficient access     
        self.metrics_by_sequence = {}   
        for metrics_path in metrics:
            metric_instance = Metric.from_dict(metrics_path)

            if metric_instance.sequence not in self.metrics_by_sequence:
                self.metrics_by_sequence[metric_instance.sequence] = []
            self.metrics_by_sequence[metric_instance.sequence].append(metric_instance)




    def __init__(self, data_path: str):
        self.data_path = os.path.normpath(data_path)
        self.read_labels()

        frame_data_files = self.get_sorted_data_files()
        self.read_captures(frame_data_files)
        self.read_metrics(frame_data_files)

    @property
    def len_sequences(self):
        return len(self.captures_by_sequence)

    @property
    def sequence_ids(self):
        return list(self.captures_by_sequence.keys())

    def get_sequence_captures(self, sequence: int) -> List[Capture]:
        """
        Get all captures in a sequence.
        :param sequence:
        :return: List of Captures
        """
        return self.captures_by_sequence[sequence]
    
    def get_sequence_metrics(self, sequence: int) -> List[MetricBase]:
        """
        Get all metrics in a sequence.
        :param sequence:
        :return: List of Metrics
        """
        return self.metrics_by_sequence[sequence]

    @property
    def captures(self):
        return [capture for sequence in self.captures_by_sequence.values() for capture in sequence]
    
    @property 
    def metrics(self):
        return [metric for sequence in self.metrics_by_sequence.values() for metric in sequence]

