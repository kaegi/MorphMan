import subprocess


def build_ui(in_file, out_file):
    stdout = subprocess.run(["pyuic5", in_file], stdout=subprocess.PIPE).stdout

    lines = stdout.decode("utf-8").replace("__relpath__", "")

    with open(out_file, "w") as sources:
        sources.write(lines)


build_ui("morph/readability.ui", "morph/readability_ui.py")
build_ui("morph/readability_settings.ui", "morph/readability_settings_ui.py")
