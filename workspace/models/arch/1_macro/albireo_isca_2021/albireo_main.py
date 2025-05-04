import os
import json
print("Hello from albireo_main.py")
import _tests
from scripts.notebook_utils import *

# Sanity check.
try:
    print(get_important_variables_markdown('albireo_isca_2021'))
except Exception as e:
    print(f"{e}")



print("Running albireo_main.py")

def simple_energy_breakdown():
    result = run_test("albireo_isca_2021", "test_energy_breakdown")
    n_subplots = len(result)
    fig, axs = plt.subplots(1, n_subplots, figsize=(5 * n_subplots, 5))
    full_data = {}
    for i, r in enumerate(result):
        print(f"Results for {r}. {type(r)}.")
        data = bar_side_by_side(
            r.get_compare_ref_energy()*1e15/r.computes,
            xlabel="Component",
            ylabel="Energy (fJ/MAC)",
            title=f"Energy Breakdown for {r.variables['scaling']} scaling",
            ax=axs[i],
        )
        full_data[r.variables["scaling"]] = data

    plt.tight_layout()
    # Save the figure
    fig.savefig("simple_energy_breakdown.png")
    # Save the data
    with open("simple_energy_breakdown.json", "w") as f:
        json.dump(full_data, f, indent=2)


def area_breakdown():
    result = run_test("albireo_isca_2021", "test_area_breakdown")
    fig, ax = plt.subplots(1, 2, figsize=(10, 5))
    full_data = {}
    data = bar_side_by_side(
        result[0].get_compare_ref_area()*1e6,
        xlabel="Component",
        ylabel="Area (mm^2)",
        title=f"Area Breakdown",
        ax=ax[0],
    )
    full_data["full"] = data
    for big_component in ["AWG", "Star Coupler", "Laser", "MZM"]:
        del result[0].per_component_area[big_component]


    data = bar_side_by_side(
        result[0].get_compare_ref_area()*1e6,
        xlabel="Component",
        ylabel="Area (mm^2)",
        title=f"Area Breakdown (excluding large components)",
        ax=ax[1],
    )
    full_data["small"] = data
    plt.tight_layout()
    # Save the figure
    fig.savefig("area_breakdown.png")
    # Save the data
    with open("area_breakdown.json", "w") as f:
        json.dump(full_data, f, indent=2)


def dnn_energy_breakdown():
    # This test may take a while to run. We have to find a mapping for every layer
    # for every DNN being tested.
    results = {}
    dnn_names = ["resnet18"]
    assert len(dnn_names) == 1, "This test only supports one DNN at a time."
    for i, dnn in enumerate(dnn_names):
        results[dnn] = run_test(
            "albireo_isca_2021", "test_full_dnn", dnn_name=dnn, show_doc=i == 0
        )
    fig, axs = plt.subplots(1, 2, figsize=(15, 5))

    tops, tops_per_w = {}, {}

    # Full-DNN results
    for dnn, r in results.items():
        tops[dnn], tops_per_w[dnn] = {}, {}
        print(f"Results for {dnn}. {type(r)}.")
        print(f"All properties: {r[0].variables.keys()}")
        print(f"Cycles: {r[0].cycle_seconds}")

    for r2 in r.aggregate_by("BATCH_SIZE"):
        batch_size = f'Batch Size {r2.variables["BATCH_SIZE"]}'
        tops[dnn][batch_size] = r2.tops
        tops_per_w[dnn][batch_size] = r2.tops_per_w

    # End-to-end results
    full_data = {}
    for ax, data, title, ylabel in [
        (axs[0], tops, "Throughput", "TOPS"),
        (axs[1], tops_per_w, "Energy Efficiency", "TOPS/W"),
    ]:
        d = bar_side_by_side(
            data,
            xlabel="DNN",
            ylabel=f"{title} ({ylabel})",
            title=f"Full-DNN {title}",
            ax=ax,
        )
        full_data[title] = d
    # Save the figure and data
    plt.tight_layout()
    fig.savefig("dnn_energy_breakdown_e2e.png")
    with open("dnn_energy_breakdown_e2e.json", "w") as f:
        json.dump(full_data, f, indent=2)

    # Per-Layer Results
    full_data = {}
    for dnn, result in results.items():
        fig, ax = plt.subplots(1, 4, figsize=(20, 5))
        for ax, attrname, title, ylabel, scaleby in [
            (ax[0], "tops", "Throughput", "TOPS", 1),
            (ax[1], "tops_per_w", "Energy Efficiency", "TOPS/W", 1),
            (ax[2], "latency", "Latency", "us", 1e6),
            (ax[3], "energy", "Total Energy", "mJ", 1e9),
        ]:
            per_layer_results = {}
            for j, same_layers in enumerate(zip(*result.split_by("BATCH_SIZE"))):
                per_layer_results[j] = {
                    f'Batch Size {r.variables["BATCH_SIZE"]}': getattr(r, attrname) * scaleby
                    for r in same_layers
                }
            d = bar_side_by_side(
                per_layer_results,
                xlabel="Layer",
                ylabel=f"{title} ({ylabel})",
                title=f"{dnn} Per-Layer {title}",
                ax=ax,
            )
            full_data[title] = d
        plt.tight_layout()
        # Save the figure
        fig.savefig(f"{dnn}_energy_breakdown_per_layer.png")
        # Save the data
        with open(f"{dnn}_energy_breakdown_per_layer.json", "w") as f:
            json.dump(full_data, f, indent=2)



def architecture_exploration():
    raw_results = run_test(
        "albireo_isca_2021", "test_explore_architectures", dnn_name="resnet18"
    )
    results = raw_results.aggregate_by("N_COLUMNS", "N_PLCU", "N_PLCG", "ADC_RESOLUTION")
    organized = {}
    for r in results:
        key = []
        key.append(f"{r.variables['N_COLUMNS']} Columns")
        key.append(f'{r.variables["N_PLCU"]} PLCUs')
        key.append(f'{r.variables["N_PLCG"]} PLCGs')
        key.append(f'{r.variables["ADC_RESOLUTION"]} bits')
        key = ", ".join(key)
        organized[key] = r

    fig, axs = plt.subplots(1, 3, figsize=(15, 5))
    full_data = {}
    d = bar_stacked(
        {k: v.per_compute("per_component_energy") for k, v in organized.items()},
        xlabel="Architecture",
        ylabel="Energy (pJ/MAC)",
        title="Per-Architecture Total Energy",
        ax=axs[0],
    )
    full_data["per_architecture"] = d

    for ax, attrname, title, ylabel in [
        (axs[1], "tops_per_w", "Energy Efficiency", "TOPS/W"),
        (axs[2], "tops_per_mm2", "Compute Density", "TOPS/mm^2"),
    ]:
        d = bar_side_by_side(
            {k: {"": getattr(v, attrname)} for k, v in organized.items()},
            xlabel="Architecture",
            ylabel=f"{title} ({ylabel})",
            title=f"Per-Architecture {title}",
            ax=ax,
        )
        full_data[title] = d
    plt.tight_layout()
    # Save the figure
    fig.savefig("architecture_exploration.png")
    # Save the data
    with open("architecture_exploration.json", "w") as f:
        json.dump(full_data, f, indent=2)


# simple_energy_breakdown()
# simple_area_breakdown()
# dnn_energy_breakdown()
architecture_exploration()