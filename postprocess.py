import argparse
import json


def calculate_median(cleared_data):
    box_sizes = []
    for i in range(len(cleared_data)):
        for j in range(len(cleared_data[i]['words'])):
            if cleared_data[i]['words'][j]['text'] != '|':
                box_size = cleared_data[i]['words'][j]['box'][3] - cleared_data[i]['words'][j]['box'][1]
                box_sizes.append(box_size)

    box_sizes.sort()
    half = len(box_sizes) // 2
    if len(box_sizes) % 2:
        median = box_sizes[half]
    else:
        median = (box_sizes[half - 1] + box_sizes[half]) / 2.0
    return median


def group_data(cleared_data, median):
    group = {}
    for i in range(len(cleared_data)):
        for j in range(len(cleared_data[i]["words"])):
            if cleared_data[i]["words"][j]["text"] != "|":
                obj = {
                    "text": cleared_data[i]["words"][j]["text"],
                    "x_bottom": cleared_data[i]["words"][j]["box"][0],
                    "y_bottom": cleared_data[i]["words"][j]["box"][1],
                    "x_top": cleared_data[i]["words"][j]["box"][2],
                    "y_top": cleared_data[i]["words"][j]["box"][3],
                    "x_middle": int(
                        (cleared_data[i]["words"][j]["box"][2] + cleared_data[i]["words"][j]["box"][0]) / 2),
                    "y_middle": int(
                        (cleared_data[i]["words"][j]["box"][3] + cleared_data[i]["words"][j]["box"][1]) / 2),
                }
                if cleared_data[i]["label"] in group:
                    added = False
                    for key in group[cleared_data[i]["label"]]:
                        for k in range(len(group[cleared_data[i]["label"]][key])):
                            if abs(obj["y_middle"] - group[cleared_data[i]["label"]][key][k]["y_middle"]) < median:
                                group[cleared_data[i]["label"]][key].append(obj)
                                added = True
                                break
                        if added:
                            break
                    if not added:
                        new_id = int(list(group[cleared_data[i]["label"]].keys())[-1]) + 1
                        group[cleared_data[i]["label"]][new_id] = [obj]
                else:
                    group[cleared_data[i]["label"]] = {1: [obj]}
    return group


def sync_names(groups):
    clean_groups = groups
    for z in range(len(clean_groups)):
        group = clean_groups[z]
        if "PER-BIRTHDAY" in group and len(group["PER-BIRTHDAY"]) == 1:
            if "PER-NAME" in group and len(group["PER-NAME"]) > 1:
                names_object = group["PER-NAME"]
                names = []
                for key in names_object:
                    for s in range(len(names_object[key])):
                        names.append(names_object[key][s])
                group["PER-NAME"] = {1: names}
        clean_groups[z] = group
    return clean_groups


if __name__ == '__main__':
    groups = []
    input_file = open('LayoutlMV3InferenceOutput.json')
    data = json.load(input_file)
    for x in data:
        median = calculate_median(x.output)
        groups.append(group_data(x.output, median))
    groups = sync_names(groups)
    inference_out = [json.dumps(groups, ensure_ascii=False)][0]
    with open('Cleaned_Group.json', 'w') as inf_out:
        inf_out.write(inference_out)




