from pychecker.check.analysis_setup_params import analysis_setup_python_requires
from pychecker.check.analysis_version_info_usage import analysis_sys_version_info
from pychecker.check.common import analysis


def detect_local_comp_detection(path):
    file = open(path)
    code = "".join(file.readlines())
    file.close()
    python_requires = analysis_setup_python_requires(code)
    use_sys_version_info = analysis(path, analysis_sys_version_info)
    if use_sys_version_info and not python_requires:
        return True
    return False


