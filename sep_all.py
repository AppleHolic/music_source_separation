import glob
import os


file_list = glob.glob('/home/appleholic/workspace/data/musics/processed/*.wav')


out_dir = '/home/appleholic/workspace/data/musics/out_samples'


new_file_list = [os.path.join(out_dir, os.path.basename(p).split('.')[0]+'_vocals.wav') for p in file_list]


print('\n'.join(new_file_list))


for in_file, out_file in zip(file_list, new_file_list):
    cmd = f"python separate_scripts/separate.py --audio_path '{in_file}' --out_path '{out_file}' --source_type vocals"
    os.system(cmd)
