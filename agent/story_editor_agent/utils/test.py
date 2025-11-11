import zipfile

with zipfile.ZipFile(r'C:\Users\udtren\Pictures\krita_test_2.kra', 'r') as kra_zip:
    all_files = kra_zip.namelist()

    print(all_files)
