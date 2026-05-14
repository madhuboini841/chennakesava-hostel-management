import os
import zipfile

def zipdir(path, ziph):
    for root, dirs, files in os.walk(path):
        if '.venv' in dirs:
            dirs.remove('.venv')
        if 'venv' in dirs:
            dirs.remove('venv')
        if '.git' in dirs:
            dirs.remove('.git')
        if 'node_modules' in dirs:
            dirs.remove('node_modules')
        for file in files:
            file_path = os.path.join(root, file)
            if "hostel_backup_12_05_2026.zip" not in file_path:
                arcname = os.path.relpath(file_path, path)
                ziph.write(file_path, arcname)

if __name__ == '__main__':
    target_zip = r"C:\Users\Madhu\OneDrive\Pictures\Desktop\hostel_backup_12_05_2026.zip"
    source_dir = r"C:\Users\Madhu\OneDrive\Pictures\Desktop\hostel fix"
    with zipfile.ZipFile(target_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipdir(source_dir, zipf)
    print(f"Project zipped successfully to {target_zip}")
