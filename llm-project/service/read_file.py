import tkinter.filedialog as filedialog
import pandas as pd

# response에 CSV 형식이 있는지 확인하고 있으면 저장하기
def save_to_csv(df):
    file_path = filedialog.asksaveasfilename(defaultextension='.csv')
    if file_path:
        df.to_csv(file_path, sep=';', index=False, lineterminator='\n')
        return f'파일을 저장했습니다. 저장 경로는 다음과 같습니다. \n {file_path}\n'
    return '저장을 취소했습니다'


def save_playlist_as_csv(playlist_csv):
    if ";" in playlist_csv:
        lines = playlist_csv.strip().split("\n")
        csv_data = []

        for line in lines:
            if ";" in line:
                csv_data.append(line.split(";"))

        if len(csv_data) > 0:
            df = pd.DataFrame(csv_data[1:], columns=csv_data[0])
            return save_to_csv(df)

    return f'저장에 실패했습니다. \n저장에 실패한 내용은 다음과 같습니다. \n{playlist_csv}'