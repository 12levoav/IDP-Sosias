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


def find_nearest(array, number):
    nearest_index = 0
    smallest_difference = abs(number - array[0])

    for i in range(1, len(array)):
        current_difference = abs(number - array[i])

        if current_difference < smallest_difference:
            smallest_difference = current_difference
            nearest_index = i

    return nearest_index


def sync_per_name(group):
    if "PER-NAME" in group and len(group["PER-NAME"]) > 1:
        names_object = group["PER-NAME"]
        names = []
        for key in names_object:
            for s in range(len(names_object[key])):
                names.append(names_object[key][s])
        return {1: names}


def sync_comp_name(group):
    if "COMP-NAME" in group and len(group["COMP-NAME"]) > 1:
        names_object = group["COMP-NAME"]
        names = []
        for key in names_object:
            for s in range(len(names_object[key])):
                names.append(names_object[key][s])
        return {1: names}


def get_rows(group):
    rows = []
    if "PER-NAME" in group:
        names = group["PER-NAME"]
        for key in names:
            middle = []
            row_arr = names[key]
            for i in range(len(row_arr)):
                middle.append(row_arr[i]["y_middle"])
            rows.append(sum(middle) / len(middle))

    if "COMP-NAME" in group:
        names = group["COMP-NAME"]
        for key in names:
            middle = []
            row_arr = names[key]
            for i in range(len(row_arr)):
                middle.append(row_arr[i]["y_middle"])
            rows.append(sum(middle) / len(middle))

    return rows


def sync_names(groups):
    clean_groups = groups
    for z in range(len(clean_groups)):
        group = clean_groups[z]
        if ("PER-BIRTHDAY" in group and len(group["PER-BIRTHDAY"]) == 1) or (
                "PER-CITY" in group and len(group["PER-CITY"]) == 1):
            if sync_per_name(group) is not None:
                group["PER-NAME"] = sync_per_name(group)
        if ("COMP-CITY" in group and (len(group["COMP-CITY"]) == 1)) or (
                "COMP-DISTRICT_COURT" in group and (len(group["COMP-DISTRICT_COURT"]) == 1)) or (
                "COMP-ID" in group and (len(group["COMP-ID"]) == 1)):
            if sync_comp_name(group) is not None:
                group["COMP-NAME"] = sync_comp_name(group)
        clean_groups[z] = group
    return clean_groups

def update_group(group, rows):
    for key in group:
        new_rows = rows.copy()

        if len(group[key]) > len(rows):
            new_obj = {}
            for inner_key in group[key]:
                inner_value = sorted(group[key][inner_key], key=lambda x: x['y_middle'], reverse=True)
                closest = find_nearest(new_rows, inner_value[0]['y_middle'])
                if inner_value[0]['y_middle'] > new_rows[closest] or closest == 0:
                    new_rows[closest] = inner_value[0]['y_middle']
                    if closest + 1 not in new_obj:
                        new_obj[closest + 1] = inner_value
                    else:
                        new_obj[closest + 1] = inner_value + new_obj[closest + 1]
                else:
                    new_rows[closest - 1] = inner_value[0]['y_middle']
                    if closest not in new_obj:
                        new_obj[closest] = inner_value
                    else:
                        new_obj[closest] = inner_value + new_obj[closest]

            group[key] = new_obj

    return group


if __name__ == '__main__':
    groups = []
    input_file = open('LayoutlMV3InferenceOutput.json')
    data = json.load(input_file)
    for x in data:
        median = calculate_median(x['output'])
        groups.append(group_data(x['output'], median))
    groups = sync_names(groups)
    for group in groups:
        rows = get_rows(group)
        group.update(update_group(group, rows))
    inference_out = [json.dumps(groups, ensure_ascii=False)][0]
    with open('Cleaned_Group.json', 'w') as inf_out:
        inf_out.write(inference_out)
