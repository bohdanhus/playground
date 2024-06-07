import os


def list_files_and_folders(path, max_recursion=1, current_recursion=0):
    if current_recursion > max_recursion:
        return

    if os.path.exists(path):
        if os.path.isdir(path):
            print(f"Directory: {path}")
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                list_files_and_folders(item_path, max_recursion, current_recursion + 1)
        else:
            print(f"File: {path}")
    else:
        print(f"Path not found: {path}")


# Пример использования:
path = r'G:\gdrive'  # Укажите путь к корневой папке Google Drive
max_recursion = 2  # Уровень рекурсии (сколько подпапок обойти)
list_files_and_folders(path, max_recursion)
