import multiprocessing
import tkinter as tk
from tkinter import filedialog, scrolledtext
import os
import sys
import threading
import traceback
from rt_utils import RTStructBuilder

sys.path.append(os.path.abspath("."))

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

from get_rt import make_rt
from gogo import simulate_pyradiomics


def get_roi_names(dicom_path):
    rtstruct = None
    for f in os.listdir(dicom_path):
        if f.lower().endswith(".dcm"):
            rtstruct = os.path.join(dicom_path, f)
            break
    if not rtstruct:
        raise FileNotFoundError("RTSTRUCT DICOM을 찾을 수 없습니다.")

    rt = RTStructBuilder.create_from(
        dicom_series_path=dicom_path, rt_struct_path=rtstruct
    )
    return rt.get_roi_names()


class AutoRadiomicsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Aura(AutoRadiomics)")
        self._build_ui()

    def _build_ui(self):

        tk.Label(self.root, text="DICOM 폴더").grid(row=0, column=0, sticky="w")
        self.dicom_dir_entry = tk.Entry(self.root, width=60)
        self.dicom_dir_entry.grid(row=0, column=1)
        tk.Button(self.root, text="찾기", command=self.choose_dicom_dir).grid(row=0, column=2)

        tk.Label(self.root, text="ROI 선택").grid(row=2, column=0, sticky="w")
        self.roi_listbox = tk.Listbox(self.root, selectmode="multiple", width=60, height=8)
        self.roi_listbox.grid(row=2, column=1, columnspan=2)

        self.start_button = tk.Button(self.root, text="시작", command=self.start_pipeline)
        self.start_button.grid(row=3, column=0, columnspan=3, pady=10)

        self.log_output = scrolledtext.ScrolledText(self.root, height=15, width=80, state='disabled')
        self.log_output.grid(row=4, column=0, columnspan=3, padx=5, pady=5)
        self.log('프로그램을 시작했습니다!')

    def log(self, message):
        self.log_output.config(state='normal')
        self.log_output.insert(tk.END, message + "\n")
        self.log_output.config(state='disabled')
        self.log_output.see(tk.END)

    def choose_dicom_dir(self):
        path = filedialog.askdirectory()
        if path:
            self.dicom_dir_entry.delete(0, tk.END)
            self.dicom_dir_entry.insert(0, os.path.normpath(path))
            try:
                roi_names = get_roi_names(path)
                self.roi_listbox.delete(0, tk.END)
                for roi in roi_names:
                    self.roi_listbox.insert(tk.END, roi)
                self.log(f"RTSTRUCT에서 {len(roi_names)}개 ROI를 불러왔습니다.")
            except Exception as e:
                self.log(f"ROI 불러오기 실패: {e}")

    def start_pipeline(self):
        dicom_path = self.dicom_dir_entry.get()
        selected_indices = self.roi_listbox.curselection()
        names = [self.roi_listbox.get(i) for i in selected_indices]
        if not names:
            self.log("ROI를 하나 이상 선택하세요.")
            return
        threading.Thread(target=self._run_pipeline, args=(dicom_path, names), daemon=True).start()

    def _run_pipeline(self, dicom_path, names):
        out_path = dicom_path
        os.makedirs(out_path, exist_ok=True)
        try:
            for name in names:
                mask_output = make_rt(dicom_path, name)
                self.log(f"[{name}] RTSTRUCT 변환 완료 ")

                out_csv = os.path.join(out_path, f"{name}_pyradiomics.csv")
                param_file = resource_path("parameters.yaml")

                simulate_pyradiomics(
                    dicom_path,
                    mask_output,
                    out_csv,
                    param_path=param_file
                )
                self.log(f"[{name}] 라디오믹스 추출 완료: {out_csv}")

        except Exception as e:
            self.log(f"에러 발생: {e}")
            self.log(traceback.format_exc())


if __name__ == "__main__":
    multiprocessing.freeze_support()
    if len(sys.argv) > 1 and sys.argv[1] == "--prevent-loop":
        sys.exit(0)
    root = tk.Tk()
    app = AutoRadiomicsApp(root)
    root.mainloop()
