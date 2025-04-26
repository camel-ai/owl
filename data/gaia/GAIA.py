"""GAIA 2023 dataset."""


import json
import os

import datasets


_CITATION = """ """

_DESCRIPTION = """ """

_HOMEPAGE = ""

_LICENSE = ""

_NAMES = [
    "2023_all",
    "2023_level1",
    "2023_level2",
    "2023_level3",
]

YEAR_TO_LEVELS = {"2023": [1, 2, 3]}

separator = "_"


class GAIA_dataset(datasets.GeneratorBasedBuilder):
    VERSION = datasets.Version("0.0.1")

    BUILDER_CONFIGS = [
        datasets.BuilderConfig(name=name, version=version, description=name)
        for name, version in zip(_NAMES, [VERSION] * len(_NAMES))
    ]

    def _info(self):
        features = datasets.Features(
            {
                "task_id": datasets.Value("string"),
                "Question": datasets.Value("string"),
                "Level": datasets.Value("string"),
                "Final answer": datasets.Value("string"), # ? for test values
                "file_name": datasets.Value("string"),
                "file_path": datasets.Value("string"),  # generated here
                "Annotator Metadata": {k: datasets.Value("string") for k in ["Steps", "Number of steps", "How long did this take?", "Tools", "Number of tools"]} # "", 
            }
        )
        return datasets.DatasetInfo(
            description=_DESCRIPTION,
            features=features,
            homepage=_HOMEPAGE,
            license=_LICENSE,
            citation=_CITATION,
        )

    def _split_generators(self, dl_manager):
        year, level_name = self.config.name.split(separator)
        if level_name == "all":
            levels = YEAR_TO_LEVELS[year]
        else:
            level_name = int(level_name.split("level")[1])
            levels = [level_name]
        print(year, level_name)

        output = []
        for split in ["test", "validation"]:
            root_file = dl_manager.download(os.path.join(year, split, "metadata.jsonl"))
            test_attached_files = {"": ""}
            with open(root_file, "r", encoding="utf-8") as f:
                for line in f:
                    cur_line = json.loads(line)
                    if cur_line["Level"] in levels and cur_line["file_name"] != "":
                        attached_file_name = cur_line["file_name"]
                        attached_file = dl_manager.download(os.path.join(year, split, attached_file_name))
                        test_attached_files[attached_file_name] = attached_file

            output.append(
                datasets.SplitGenerator(
                    name=getattr(datasets.Split, split.upper()),
                    gen_kwargs={"root_file": root_file, "attached_files": test_attached_files, "levels": levels},
                )
            )
        return output

    # method parameters are unpacked from `gen_kwargs` as given in `_split_generators`
    def _generate_examples(self, root_file: str, attached_files: dict, levels: list[int]):
        with open(root_file, "r", encoding="utf-8") as f:
            for key, line in enumerate(f):
                cur_line = json.loads(line)
                if cur_line["Level"] in levels:
                    cur_line["file_path"] = attached_files[cur_line["file_name"]]
                    yield key, cur_line


