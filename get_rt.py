import os
import SimpleITK as sitk
from rt_utils import RTStructBuilder
import numpy as np

def load_ct_and_rt(parent_path):
  
    ct_folders = []
    rt_files = []

    for item in os.listdir(parent_path):
        full_path = os.path.join(parent_path, item)
        if os.path.isdir(full_path):
            ct_folders.append(full_path)
        elif os.path.isfile(full_path) and item.lower().endswith(".dcm"):
            rt_files.append(full_path)

    if not ct_folders:
        raise RuntimeError("DICOM 시리즈 폴더를 찾을 수 없습니다.")
    if not rt_files:
        raise RuntimeError("RT DICOM 파일을 찾을 수 없습니다.")
    
    ct_folder = max(ct_folders, key=lambda d: len(os.listdir(d)))

    rt_file = rt_files[0]

    reader = sitk.ImageSeriesReader()
    series_ids = reader.GetGDCMSeriesIDs(ct_folder)
    if not series_ids:
        raise RuntimeError(f"{ct_folder} 안에서 DICOM 시리즈를 찾을 수 없습니다.")

    dicom_files = reader.GetGDCMSeriesFileNames(ct_folder, series_ids[0])
    reader.SetFileNames(dicom_files)
    ct_image = reader.Execute()

    return ct_image, ct_folder, rt_file

def make_rt(dicom_path, name):
    ref_image, ct_folder, rt_file = load_ct_and_rt(dicom_path)
    rt = RTStructBuilder.create_from(ct_folder, rt_file)
    mask_np = rt.get_roi_mask_by_name(name)

    def npmask_to_sitk(mask_np, ref_img):
        if mask_np.shape[0] != ref_img.GetDepth():
            mask_np = np.transpose(mask_np, (2, 1, 0))
        img = sitk.GetImageFromArray(mask_np.astype(np.uint8))
        img.CopyInformation(ref_img)
        return img
    mask = npmask_to_sitk(mask_np, ref_image)

    return mask
