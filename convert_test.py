#%%
#import shapely
import src.data.unity_data as UnityData
import os
from src.data.yolo_conversion.convert_modular import unity_to_yolo
from src.data.yolo_conversion.pose import unity_to_yolo_pose

#%%
path = "C:/Users/Christoph Rüger/AppData/LocalLow/DefaultCompany/Prototyping/"
dataset_folder_name = "solo_203"
os.chdir(path)

data = UnityData.UnityData(dataset_folder_name)

#%%
#data.sequences[0][0].instance_segmentation.instances[0]

# Next: Implement visibility to the capture class. Handle missing features/data enties robustly
# Then: write custom converter similar to the one in n_pose_conversion

metrics = data.metrics_by_sequence[1]
occlusion_metric = next((metric for metric in metrics if metric.id == "Occlusion"), None)

occlusion_metric.occlusion_metric.values


#%%
output_path = dataset_folder_name + "_yolo"
os.makedirs(output_path, exist_ok=True)
#unity_to_yolo(data, output_path, include_bboxes=True, include_keypoints=False, include_segmentation=True, include_semantic_mask=True, include_occlusion=True, include_test=False, precision=6)
unity_to_yolo(data, output_path, include_bboxes=True, include_keypoints=False, include_segmentation=False, include_semantic_mask=False, include_occlusion=True, include_test=False, precision=6)
#unity_to_yolo_pose(data, output_path, n_keypoints=17, flip_idx=[1, 2, 3, 4, 5, 6, 11, 12, 13, 14, 15, 16], include_test=False, precision=6)
