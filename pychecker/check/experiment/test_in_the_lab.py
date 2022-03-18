import os
from pychecker.check.extra_dep_detection import detect_extra_deps
from pychecker.check.local_comp_detection import detect_local_comp_detection
from pychecker.check.incomp_feature_detection import detect_incomp_feature_usage
from pychecker.check.no_avl_resource_detection import detect_no_avl_resource_pkg
from pychecker.check.common import parse_custom_modules
from pychecker.utils import read_object_from_file
from pychecker.check.experiment.exp_config import IN_THE_LAB_ROOT


class Test:
    def __init__(self, func):
        print("\033[0m", "-"*10, self.__class__.__name__, "-"*10)
        self.root = IN_THE_LAB_ROOT
        self.mapping = {detect_incomp_feature_usage: 1,
                        detect_extra_deps: 2,
                        detect_local_comp_detection: 3,
                        detect_no_avl_resource_pkg: 4}
        self.func = func
        self.data = self.prepare_data()
        self.result_mat = list()  # [(answer, my_answer), ]

    def prepare_data(self):
        meta_path = os.path.join(self.root, "answer.txt")
        with open(meta_path) as f:
            metadata = f.readlines()[1:]
        data = dict()
        col = self.mapping[self.func]
        for row in metadata:
            row = row.strip()
            parts = row.split(",")
            project, answer = parts[0], parts[col]
            answer = True if answer == "1" else False
            data[project] = answer
        return data

    def test(self, start=None, end=None):
        if not start:
            start = 0
        if not end:
            end = len(self.data.items())
        for ind, (project, answer) in enumerate(list(self.data.items())[start:end]):
            my_answer = self.test_item(project)
            result = True if my_answer == answer else False
            color = "\033[32m" if result else "\033[31m"
            print(color, f"{ind:2}", project, result)
            self.result_mat.append((answer, my_answer))
        self.statistic()

    def statistic(self):
        tp, fp, tn, fn = 0, 0, 0, 0
        correct = 0
        for item in self.result_mat:
            tp += 1 if item[0] and item[0] == item[1] else 0
            tn += 1 if item[0] and item[0] != item[1] else 0
            fn += 1 if not item[0] and item[0] == item[1] else 0
            fp += 1 if not item[0] and item[0] != item[1] else 0
            correct += 1 if item[0] == item[1] else 0
        acc = correct/len(self.result_mat)
        pre = tp/(tp+fp) if tp+fp != 0 else 0
        rec = tp/(tp+tn) if tp+tn != 0 else 0
        f1 = 2*pre*rec/(pre+rec) if pre+rec != 0 else 0
        color = "\033[0m"
        print(color)
        print("         \t True \t False")
        print(" Positive\t", tp, " \t", fp)
        print(" Negative\t", tn, " \t", fn)
        print(" acc:", acc, "\n pre:", pre, "\n rec:", rec, "\n f1-score:", f1)

    def test_item(self, project):
        return True


class LocalCompTest(Test):
    def __init__(self):
        super().__init__(detect_local_comp_detection)

    def test_item(self, project):
        setup_path = os.path.join(self.root, project, "setup.py")
        return detect_local_comp_detection(setup_path)


class ExtraDepTest(Test):
    def __init__(self):
        super().__init__(detect_extra_deps)

    def test_item(self, project):
        setup_path = os.path.join(self.root, project, "setup.py")
        local_modules = parse_custom_modules(os.path.dirname(setup_path))
        return detect_extra_deps(setup_path, custom_modules=local_modules)


class IncompTest(Test):
    def __init__(self):
        super().__init__(detect_incomp_feature_usage)
        comp_info_path = os.path.join(self.root, "compatibility.json")
        self.comp_info = read_object_from_file(comp_info_path)

    def test_item(self, project):
        setup_path = os.path.join(self.root, project, "setup.py")
        comp_info = self.comp_info[project]
        local_modules = parse_custom_modules(os.path.dirname(setup_path))
        return detect_incomp_feature_usage(setup_path, comp_info, local_modules)


class NoAvlTest(Test):
    def __init__(self):
        super().__init__(detect_no_avl_resource_pkg)

    def test_item(self, project):
        parts = project.split("-")
        pkg = "-".join(parts[:-1])
        ver = parts[-1]
        return detect_no_avl_resource_pkg(pkg, ver)


def generate_result(tests, output_path):
    result = list()
    for ind, project in enumerate(tests[0].data.keys()):
        line = f"{project}"
        for test in tests:
            res = test.result_mat[ind]
            line += f",{int(res[1])}"
        line += "\n"
        result.append(line)

    with open(output_path, "w") as f:
        f.writelines(result)


if __name__ == '__main__':
    testA = LocalCompTest()
    testA.test()
    # testB = ExtraDepTest()
    # testB.test()
    testC = IncompTest()
    testC.test()
    testD = NoAvlTest()
    testD.test()
    generate_result([testC, testA, testD], "./result-lab.csv")