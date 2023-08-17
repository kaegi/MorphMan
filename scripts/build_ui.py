import subprocess

def build_ui(in_file, out_file):
    stdout = subprocess.Popen(["pyuic6", in_file], stdout=subprocess.PIPE, text=True).stdout

    with open(out_file, 'w') as sources:
        for line in iter(stdout.readline, ""):
            if line.startswith("from PyQt6 import"):
                imports = line.split("import")[1].strip()
                sources.write(f"""try:
    from PyQt6 import {imports}
except:
    from PyQt5 import {imports}
""")
            else:
                sources.write(line)

build_ui("morph/readability.ui", "morph/readability_ui.py")
build_ui("morph/readability_settings.ui", "morph/readability_settings_ui.py")
