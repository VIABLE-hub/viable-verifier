import pandas as pd
import matplotlib.pyplot as plt


data = pd.read_csv("benchmark_results.csv")
# df = pd.DataFrame(columns=["class_name", "loop_count",
#                     "variance_description", "variance_value", "variance_title", "time"])


# split dataframe into key generation and everything else
key_generation = data[data["variance_title"] == "Key Generation Benchmark"]
data = data[data["variance_title"] != "Key Generation Benchmark"]


# !IMPORTANT! assume loop_count is the same for all variance_title
all_variance_titles = data["variance_title"].unique()
loop_counts = data["loop_count"].unique()

# create a subplot for each variance_title + 1(key generation)
fig, axs = plt.subplots(len(loop_counts), len(
    all_variance_titles) + 1, figsize=(80, 20))
plt.subplots_adjust(hspace=0.4)


for row_index, loop_count in enumerate(loop_counts):
    # Add row title

    # plot key generation
    for credential_class in key_generation["class_name"].unique():
        X = key_generation[key_generation["class_name"]
                           == credential_class]["loop_count"]
        Y = key_generation[key_generation["class_name"]
                           == credential_class]["time"]
        axs[row_index, 0].plot(X, Y, label=credential_class)
    axs[row_index, 0].set_title(key_generation["variance_title"].unique()[0])
    axs[row_index, 0].set_xlabel(
        key_generation["variance_description"].unique()[0])
    axs[row_index, 0].set_ylabel("Time in seconds")
    axs[row_index, 0].legend()

    current_data = data[data["loop_count"] == loop_count]
    # plot everything else
    for col_index, variance_title in enumerate(all_variance_titles):
        for credential_class in data["class_name"].unique():

            X = current_data[(current_data["class_name"] == credential_class) & (
                current_data["variance_title"] == variance_title)]["variance_value"]
            Y = current_data[(current_data["class_name"] == credential_class) & (
                current_data["variance_title"] == variance_title)]["time"]
            Y = Y / loop_count
            axs[row_index, col_index + 1].plot(X, Y, label=credential_class)
        axs[row_index, col_index + 1].set_title(variance_title)
        variance_description = current_data[current_data["variance_title"] == variance_title][
            "variance_description"].unique()[0]

        axs[row_index, col_index + 1].set_xlabel(variance_description)
        axs[row_index, col_index + 1].set_ylabel("Time in seconds")
        axs[row_index, col_index + 1].legend()


pad = 5  # in points

rows = data["loop_count"].unique()
rows = [f"Loop count: {row}" for row in rows]
for ax, row in zip(axs[:, 0], rows):
    ax.annotate(row, xy=(0, 0.5), xytext=(-ax.yaxis.labelpad - pad, 0),
                xycoords=ax.yaxis.label, textcoords='offset points',
                size='large', ha='right', va='center')

plt.show()
