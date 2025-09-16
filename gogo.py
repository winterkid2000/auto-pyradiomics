import os
import SimpleITK as sitk
from radiomics import featureextractor
import pandas as pd

def load_ct(parent_path: str):
  
    ct_folders = [
        os.path.join(parent_path, f) 
        for f in os.listdir(parent_path) 
        if os.path.isdir(os.path.join(parent_path, f))
    ]
    if not ct_folders:
        raise RuntimeError("DICOM 시리즈 폴더를 찾을 수 없습니다.")

    ct_folder = max(ct_folders, key=lambda d: len(os.listdir(d)))

    reader = sitk.ImageSeriesReader()
    dicom_names = reader.GetGDCMSeriesFileNames(ct_folder)
    reader.SetFileNames(dicom_names)
    image = reader.Execute()
    return image

def simulate_pyradiomics(dicom_path: str, mask: sitk.Image, output_csv: str, param_path: str):

    if not os.path.exists(param_path):
        raise FileNotFoundError(f"YAML 파일을 찾을 수 없습니다: {param_path}")

    dicom_image = load_ct(dicom_path)

    extractor = featureextractor.RadiomicsFeatureExtractor(param_path)

    features = extractor.execute(dicom_image, mask)

    df = pd.DataFrame([features])
    df.to_csv(output_csv, index=False)

    print(f"Radiomics features saved to {output_csv}")
    return output_csv
