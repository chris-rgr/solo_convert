import os
import shutil
from typing import List, Optional, Dict

import cv2
from progressbar import ProgressBar

from ..unity_data import Capture, UnityData
from ...util import generate_random_split, detect_colored_polygons
from .data_directory import create_yolo_data_dir

def get_bbox_annotations(capture: Capture, precision: int = 6) -> List[str]:
    """
    Get 2D bounding box annotations for a single capture.
    """
    annotations = []
    img_width = capture.dimension[0]
    img_height = capture.dimension[1]

    for bounding_box in capture.bounding_boxes_2d.values:
        center_x = round((bounding_box.origin[0] + bounding_box.dimension[0] / 2) / img_width, precision)
        center_y = round((bounding_box.origin[1] + bounding_box.dimension[1] / 2) / img_height, precision)
        width = round(bounding_box.dimension[0] / img_width, precision)
        height = round(bounding_box.dimension[1] / img_height, precision)
        
        annotations.append(f"{bounding_box.label.id} {center_x} {center_y} {width} {height}")

    return annotations

def get_keypoint_annotations(capture: Capture, precision: int = 6) -> List[str]:
    """
    Get keypoint annotations for a single capture, including their associated bounding boxes.
    """
    annotations = []
    img_width = capture.dimension[0]
    img_height = capture.dimension[1]

    for bounding_box in capture.bounding_boxes_2d.values:
        keypoint_annotation = next(
            (kp for kp in capture.keypoints.values if kp.instance_id == bounding_box.instance_id), None)
        
        if keypoint_annotation is None:
            continue

        # Calculate normalized bounding box coordinates
        center_x = round((bounding_box.origin[0] + bounding_box.dimension[0] / 2) / img_width, precision)
        center_y = round((bounding_box.origin[1] + bounding_box.dimension[1] / 2) / img_height, precision)
        width = round(bounding_box.dimension[0] / img_width, precision)
        height = round(bounding_box.dimension[1] / img_height, precision)

        # Process keypoints
        keypoints = []
        for keypoint in keypoint_annotation.keypoints:
            keypoint_x = round(keypoint.location[0] / img_width, precision)
            keypoint_y = round(keypoint.location[1] / img_height, precision)
            keypoint_visible = 1 if keypoint.state == 2 else 0
            keypoints.append(f"{keypoint_x} {keypoint_y} {keypoint_visible}")

        annotations.append(f"{bounding_box.label.id} {center_x} {center_y} {width} {height} {' '.join(keypoints)}")

    return annotations

def get_segmentation_annotations(capture: Capture, precision: int = 6) -> List[str]:
    """
    Get segmentation annotations for a single capture.
    """
    annotations = []
    if capture.instance_segmentation is None:
        return annotations

    img = cv2.imread(capture.instance_segmentation.file_path)
    instances = capture.instance_segmentation.instances

    for instance in instances:
        _, norm_polygons = detect_colored_polygons(img, instance.color, precision=precision)

        annotation = f'{instance.label.id}'
        for polygon in norm_polygons:
            boundary_x = polygon.boundary.coords.xy[0]
            boundary_y = polygon.boundary.coords.xy[1]

            coord_pairs = []
            for n, x in enumerate(boundary_x):
                y = boundary_y[n]
                coord_pairs.append(f'{x} {y}')

            annotation += f' {" ".join(coord_pairs)}'

        annotations.append(annotation)

    return annotations

def write_yaml_header(yaml_path: str, unity_data: UnityData, *, 
                     include_keypoints: bool = False,
                     n_keypoints: Optional[int] = None,
                     flip_idx: Optional[List[int]] = None,
                     include_test: bool = False) -> None:
    """
    Write the YAML header file with dataset configuration.
    """
    with open(yaml_path, "w") as f:
        # Write metadata
        f.write(f"path: {os.path.abspath(os.path.dirname(yaml_path))}\n")
        f.write(f"train: train\n")
        f.write(f"val: val\n")
        if include_test:
            f.write(f"test: test\n")

        f.write('\n')
        
        if include_keypoints and n_keypoints is not None:
            f.write(f'kpt_shape: [{n_keypoints},3]\n')
            if flip_idx is not None:
                f.write(f'flip_idx: {flip_idx}\n')

        f.write("names:\n")
        for label in unity_data.labels:
            f.write(f"    {label.id}: {label.name}\n")

def unity_to_yolo(unity_data: UnityData, 
                 output_path: str, 
                 *,
                 include_bboxes: bool = False,
                 include_keypoints: bool = False,
                 include_segmentation: bool = False,
                 include_semantic_mask: bool = False,
                 include_occlusion: bool = False,
                 n_keypoints: Optional[int] = None,
                 flip_idx: Optional[List[int]] = None,
                 include_test: bool = False,
                 precision: int = 6) -> str:
    """
    Convert Unity data to YOLO format with configurable annotation types.
    
    Args:
        unity_data: The UnityData to convert
        output_path: Directory to save the converted dataset
        include_bboxes: Include 2D bounding boxes
        include_keypoints: Include keypoint annotations
        include_segmentation: Include segmentation annotations
        n_keypoints: Number of keypoints (required if including keypoints)
        flip_idx: Keypoint flip indices (optional)
        include_test: Whether to include a test set
        precision: Floating point precision
        
    Returns:
        Path to the generated YAML file
    """
    if include_keypoints and n_keypoints is None:
        raise ValueError("n_keypoints must be specified when include_keypoints is True")

    path, yaml_path = create_yolo_data_dir(output_path, include_test)
    write_yaml_header(yaml_path, unity_data, 
                     include_keypoints=include_keypoints,
                     n_keypoints=n_keypoints,
                     flip_idx=flip_idx,
                     include_test=include_test)

    # Collect captures with valid annotations based on config
    valid_captures = []
    for capture in unity_data.captures:
        is_valid = True
        if include_bboxes or include_keypoints:
            is_valid = is_valid and capture.bounding_boxes_2d is not None
        if include_keypoints:
            is_valid = is_valid and capture.keypoints is not None
        if include_segmentation:
            is_valid = is_valid and capture.instance_segmentation is not None
        if include_semantic_mask:
            is_valid = is_valid and capture.semantic_segmentation is not None

        if is_valid:
            valid_captures.append(capture)

    #valid_metrics = []
    #for metric in unity_data.metrics:
    #    is_valid = True
    #    if include_occlusion:
    #        is_valid = is_valid and metric.occlusion is not None
#
 #       if is_valid:
  #          valid_metrics.append(metric)

   # if len(valid_captures) != len(valid_metrics):
    #    raise ValueError("Number of valid captures and metrics must match")

    split = generate_random_split(len(valid_captures), 0.1, 0.1 if include_test else 0.0)

    with ProgressBar(max_value=len(split)) as bar:
        for i, s in enumerate(split):
            bar.update(i)
            capture = valid_captures[i]

            # Copy image file
            img_ext = capture.file_path.split(".")[-1]
            shutil.copyfile(capture.file_path, os.path.join(path, s, f'{i}.{img_ext}'))

            annotations_bbox = []
            annotations_keypoints = []
            annotations_segmentation = []
            
            # Collect all requested annotations
            if include_bboxes and not include_keypoints:
                annotations_bbox.extend(get_bbox_annotations(capture, precision))
            if include_keypoints:
                annotations_keypoints.extend(get_keypoint_annotations(capture, precision))
            if include_segmentation:
                annotations_segmentation.extend(get_segmentation_annotations(capture, precision))

            # Write annotations to file
            if annotations_bbox:
                with open(os.path.join(path, s, f'{i}_bbox.txt'), "w") as f:
                    for annotation in annotations_bbox:
                        f.write(f"{annotation}\n")
            if annotations_keypoints:
                with open(os.path.join(path, s, f'{i}_keypoints.txt'), "w") as f:
                    for annotation in annotations_keypoints:
                        f.write(f"{annotation}\n")
            if annotations_segmentation:
                with open(os.path.join
                (path, s, f'{i}_segmentation.txt'), "w") as f:
                    for annotation in annotations_segmentation:
                        f.write(f"{annotation}\n")



            metrics = unity_data.metrics_by_sequence[capture.sequence]
            occlusion_metric = next((metric for metric in metrics if metric.id == "Occlusion"), None).occlusion_metric

            # Write occlusion metrics to file
            if include_occlusion and occlusion_metric is not None and hasattr(occlusion_metric, "values") and occlusion_metric.values is not None:
                #occlusion_metric = next((metric for metric in unity_data.metrics if (metric.id == "occlusion" and metric.sequence == capture.sequence)), None)
            
                with open(os.path.join(path, s, f'{i}_occlusion.txt'), "w") as f:
                    for occlusion in occlusion_metric.values:
                        f.write(f"{occlusion.instance_id} {occlusion.percent_visible}\n")

            # Copy semantic mask
            if include_semantic_mask and capture.semantic_segmentation is not None:
                _, mask_ext = os.path.splitext(capture.semantic_segmentation.file_path)
                shutil.copyfile(capture.semantic_segmentation.file_path, os.path.join(path, s, f'{i}_mask.{mask_ext}'))

    return yaml_path